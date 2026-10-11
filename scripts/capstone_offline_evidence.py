#!/usr/bin/env python3
"""Evidence for embeddings retrieval, feedback adaptation and PII-safe logging. Runs in-process on a throwaway DB.

  PYTHONPATH=backend python scripts/capstone_offline_evidence.py retrieval    # lexical vs embeddings, with/without retrieval
  PYTHONPATH=backend python scripts/capstone_offline_evidence.py adaptation   # feedback before/after
  PYTHONPATH=backend python scripts/capstone_offline_evidence.py privacy      # redaction in logs and audit records

Requires Ollama on 11434 with `nomic-embed-text` (embeddings) and `qwen2.5:1.5b` (answers).
"""
import json
import logging
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

TMP = tempfile.mkdtemp()
os.environ.update(DATABASE_URL=f"sqlite:///{TMP}/evidence.db", EMBEDDING_BASE_URL="http://localhost:11434/v1",
                  EMBEDDING_MODEL="nomic-embed-text")

from app import feedback, incident_cases as ic  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app import models  # noqa: E402,F401
from app.redaction import install_log_redaction  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "docs" / "evidence"
CHAT = "http://127.0.0.1:11434/v1/chat/completions"

# Paraphrases that deliberately avoid the words used in the case library.
LABELLED = [
    ("Containers are being terminated for using more RAM than allowed since the last release", "SYN-K8S-001"),
    ("Everything is slow because requests queue waiting for a free handle to the data store", "SYN-APP-001"),
    ("Calls to our partner started failing because a security document lapsed", "SYN-NET-002"),
    ("A single bad record keeps getting reprocessed and nothing behind it moves", "SYN-QUEUE-002"),
    ("Monitoring graph went flat and we assumed errors stopped, but the target vanished", "SYN-OBS-001"),
    ("Pods keep getting killed by the health check before the app finishes booting", "SYN-K8S-003"),
    ("Our login to the database stopped working after credentials were changed", "SYN-DEPLOY-002"),
    ("Users behind the office network are all getting blocked with 429", "SYN-APP-010"),
]
MISSING = ["The marketing site hero image is blurry on mobile phones", "What is the best pizza topping"]


def setup():
    Base.metadata.create_all(engine)
    ic.seed_demo_cases()


def emit(name, lines):
    OUT.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    (OUT / name).write_text(text)
    print(text)


def ask(system, question):
    body = {"model": "qwen2.5:1.5b", "temperature": 0, "messages": [
        {"role": "system", "content": system}, {"role": "user", "content": question}]}
    req = urllib.request.Request(CHAT, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip().replace("\n", " ")


def retrieval():
    setup()
    lines = ["# Embedding retrieval evidence", f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}; embeddings `nomic-embed-text` "
             f"via Ollama; 34-case library; similarity floor {settings.embedding_min_similarity}_", "",
             "## 1. Lexical vs embedding top-1 (8 paraphrased queries that reuse none of the library's wording)", "",
             "| Query | Expected | Lexical top-1 | Embedding top-1 (cosine) |", "|---|---|---|---|"]
    lex_hits = sem_hits = 0
    for query, expected in LABELLED:
        lex = ic.search_incident_cases(query, 1)
        sem = ic.semantic_search_incident_cases(query, 1)
        lex_id = lex[0]["case_id"] if lex else "none"
        sem_id = sem[0]["case_id"] if sem else "none"
        lex_hits += lex_id == expected
        sem_hits += sem_id == expected
        lines.append(f"| {query} | {expected} | {lex_id} {'✅' if lex_id == expected else '❌'} | "
                     f"{sem_id} ({sem[0]['retrieval_score'] if sem else '-'}) {'✅' if sem_id == expected else '❌'} |")
    lines += ["", f"**Top-1 accuracy: lexical {lex_hits}/{len(LABELLED)}, embeddings {sem_hits}/{len(LABELLED)}.**", "",
              "## 2. Missing information: queries with no relevant precedent", "",
              "| Query | Lexical returns | Embeddings return |", "|---|---|---|"]
    for query in MISSING:
        lex = ic.search_incident_cases(query, 1)
        sem = ic.semantic_search_incident_cases(query, 1)
        lines.append(f"| {query} | {lex[0]['case_id'] + ' (irrelevant match)' if lex else 'nothing'} | "
                     f"{sem[0]['case_id'] if sem else 'nothing, below the similarity floor'} |")
    lines += ["", "Embeddings let the agent say 'no precedent found' instead of presenting an unrelated case.", "",
              "## 3. Answer quality with and without retrieval (qwen2.5:1.5b, temperature 0)", ""]
    system = ("You are an SRE assistant. Answer in two sentences. Context, when given, describes a PAST incident: use it only "
              "as a hypothesis to check, never say the cause is confirmed for this one. Without context, say the cause is unconfirmed.")
    for query, expected in LABELLED[:2]:
        top = ic.retrieve_cases(query, 1)
        case = top[0]
        context = (f"Synthetic precedent {case['case_id']}: {case['title']}. Root cause then: {case['root_cause']} "
                   f"Remediation then: {'; '.join(case['remediation'])}")
        lines += [f"**Question:** {query}", "",
                  f"- Without retrieval: {ask(system, query)}",
                  f"- With retrieval ({case['case_id']}): {ask(system + ' Context: ' + context, query)}", ""]
    lines += ["Caveat: the 1.5B local model is inconsistent in how it uses context (it can ignore it or state a past cause as fact). "
              "Retrieval is therefore also shown to the user as labelled synthetic precedents in the evidence panel; the answer text "
              "is not the proof of retrieval quality, section 1 is."]
    emit("embedding-retrieval.md", lines)


def adaptation():
    setup()
    query = "checkout-api pods keep restarting and are OOMKilled after the memory limit was lowered"
    lines = ["# Feedback adaptation evidence", f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}_", "",
             f"Query: `{query}`", "", "Feedback stores only a case id, an optional investigation id and a +1/-1 rating "
             "(no free text, so nothing personal is stored). Net votes are clamped to ±3 and scale a case's score by "
             "`1 + 0.15 × votes`.", ""]

    def table(title):
        rows = ic.retrieve_cases(query, 4)
        lines.extend([f"## {title}", "", "| Rank | Case | Score | Net votes |", "|---|---|---|---|"])
        lines.extend(f"| {i} | {c['case_id']} {c['title']} | {c['retrieval_score']} | {c['feedback_net']} |"
                     for i, c in enumerate(rows, 1))
        lines.append("")
        return rows

    before = table("Before feedback")
    wrong = before[0]["case_id"]
    for _ in range(3):
        feedback.record_feedback(wrong, helpful=False)
    lines.append(f"Reviewers mark `{wrong}` not helpful 3 times.\n")
    after = table("After feedback")
    runner = before[1]["case_id"]
    for _ in range(2):
        feedback.record_feedback(runner, helpful=True)
    lines.append(f"Reviewers mark `{runner}` helpful 2 times.\n")
    table("After positive feedback")
    ranked = [c["case_id"] for c in ic.retrieve_cases(query, 40)]
    lines.append(f"`{wrong}` (net votes -3) is now ranked {ranked.index(wrong) + 1} of {len(ranked)} candidates, down from 1.\n")
    lines += ["## What changed and why", "",
              f"- Top-1 moved from `{before[0]['case_id']}` to `{after[0]['case_id']}` after negative feedback; ranking changes only the order of precedents.",
              "- Limits: ratings are global, not per user or per service; clamping keeps a crowd of votes from hiding the best match; "
              "feedback never changes guardrail decisions, which stay deterministic."]
    emit("feedback-adaptation.md", lines)


def privacy():
    from app.repository import repo
    install_log_redaction()
    log_file = Path(TMP) / "guardian.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger = logging.getLogger("guardian.privacy-demo")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    secret_text = ("Investigating for jane.doe@example.com from 10.20.30.40, call +1 415 555 0134, "
                   "card 4111 1111 1111 1111, password=hunter2, Authorization: Bearer abcdefghijklmnop123456")
    logger.warning("user request: %s", secret_text)
    handler.flush()
    Base.metadata.create_all(engine)
    repo.audit("demo.privacy", "tester", "ENT-1", {"comment": secret_text})
    audit_row = json.dumps(repo.audit_events()[0]["payload"]) if hasattr(repo, "audit_events") else None
    if audit_row is None:
        from sqlalchemy import select
        from app.db import SessionLocal
        from app.models import AuditEvent
        with SessionLocal() as db:
            audit_row = json.dumps(db.scalars(select(AuditEvent)).first().payload)
    logged = log_file.read_text().strip()
    leaked = [token for token in ("jane.doe", "10.20.30.40", "415 555", "4111", "hunter2", "abcdefghijklmnop") if token in logged + audit_row]
    lines = ["# PII-safe logging evidence", f"_Generated {time.strftime('%Y-%m-%d %H:%M:%S')}_", "",
             "Input contained synthetic values for an email, IP address, phone number, card number, password and bearer token "
             "(raw values are intentionally not reproduced here).", "", "Log line written to disk:", "", f"```\n{logged}\n```", "",
             "Audit record payload stored in the database:", "", f"```\n{audit_row}\n```", "",
             f"Sensitive values found in either: **{leaked or 'none'}**."]
    emit("pii-safe-logging.md", lines)
    assert not leaked, leaked


if __name__ == "__main__":
    modes = {"retrieval": retrieval, "adaptation": adaptation, "privacy": privacy}
    if len(sys.argv) != 2 or sys.argv[1] not in modes:
        sys.exit(f"usage: {sys.argv[0]} {{{'|'.join(modes)}}}")
    modes[sys.argv[1]]()
