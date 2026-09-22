"""Persisted, read-only SRE conversations with optimistic turn concurrency."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, update

from .db import SessionLocal
from .models import Conversation
from .live_telemetry import investigate_live
from .conversation_engine import build_reply

MAX_MESSAGES = 60


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(value):
    return value.replace(tzinfo=timezone.utc).isoformat() if value.tzinfo is None else value.isoformat()


def serialize(row):
    return {key: getattr(row, key) for key in (
        'id', 'application', 'environment', 'namespace', 'telemetry_mode',
        'revision', 'messages', 'context', 'result')} | {'updated_at': timestamp(row.updated_at),
            'title': row.messages[0]['content'][:120] if row.messages else row.application}


def get_conversation(conversation_id):
    with SessionLocal() as db:
        row = db.get(Conversation, conversation_id)
        if row is None:
            raise HTTPException(404, 'Conversation not found')
        return serialize(row)


def list_conversations():
    with SessionLocal() as db:
        rows = db.scalars(select(Conversation).order_by(Conversation.updated_at.desc()).limit(50)).all()
        return [{key: getattr(row, key) for key in (
            'id', 'application', 'environment', 'namespace', 'telemetry_mode', 'revision')}
                | {'updated_at': timestamp(row.updated_at),
                   'title': row.messages[0]['content'][:120] if row.messages else row.application}
                for row in rows]


def collect_snapshot(scope, question):
    state = {**scope, 'query': question}
    if scope['telemetry_mode'] == 'live':
        result = investigate_live(state)
    else:
        # Sample evidence only. Never enter the demo approval/remediation graph for chat.
        from .agents.diagnostic import RCAAgent
        result = RCAAgent().execute({'evidence': []}).data
        result['guardrail'] = {'decision': 'READ_ONLY', 'reason': 'Conversation demo; no actions are executed.', 'approval_required': False}
    return {**result, 'telemetry_mode': scope['telemetry_mode'], 'snapshot_at': utcnow().isoformat()}


def user_message(text):
    return {'role': 'user', 'content': text, 'created_at': utcnow().isoformat()}


def assistant_message(reply):
    return {'role': 'assistant', 'content': reply['content'], 'question': reply.get('question'),
            'assistant_mode': reply['assistant_mode'], 'notice': reply.get('notice'), 'created_at': utcnow().isoformat()}


def start_conversation(request):
    scope = request.model_dump(exclude={'message'})
    messages = [user_message(request.message)]
    result = collect_snapshot(scope, request.message)
    reply = build_reply(messages, {}, result, scope)
    messages.append(assistant_message(reply))
    with SessionLocal() as db:
        row = Conversation(id=f'CHAT-{uuid4().hex[:12].upper()}', **scope, revision=1,
                           messages=messages, context=reply['context'], result=result)
        db.add(row)
        db.commit()
        db.refresh(row)
        return serialize(row)


def continue_conversation(conversation_id, request):
    current = get_conversation(conversation_id)
    if request.expected_revision != current['revision']:
        raise HTTPException(409, 'This conversation has a newer reply. Reload it before sending again.')
    if len(current['messages']) >= MAX_MESSAGES:
        raise HTTPException(422, 'This conversation reached 30 exchanges. Start a new conversation.')
    scope = {key: current[key] for key in ('application', 'environment', 'namespace', 'telemetry_mode')}
    messages = [*current['messages'], user_message(request.message)]
    context = dict(current['context'])
    result = current['result']
    if request.refresh_metrics:
        result = collect_snapshot(scope, context.get('original_problem', current['messages'][0]['content']))
        context['_refresh_metrics'] = True
    reply = build_reply(messages, context, result, scope)
    clean_context = {key: value for key, value in reply['context'].items() if not key.startswith('_')}
    messages.append(assistant_message(reply))
    with SessionLocal() as db:
        saved = db.execute(update(Conversation).where(
            Conversation.id == conversation_id, Conversation.revision == request.expected_revision
        ).values(messages=messages, context=clean_context, result=result,
                 revision=request.expected_revision+1, updated_at=utcnow()))
        if saved.rowcount != 1:
            db.rollback()
            raise HTTPException(409, 'Another reply was saved. Reload the conversation before sending again.')
        db.commit()
        return serialize(db.get(Conversation, conversation_id))
