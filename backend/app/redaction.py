"""Redact personal and secret data before it reaches logs or audit records."""
import logging
import re

_STANDARD_RECORD_FIELDS = frozenset(
    logging.LogRecord('', 0, '', 0, '', (), None).__dict__
)

# Order matters: secrets first, so a token containing digits is not partially matched as a phone number.
_PATTERNS = [
    (re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}"), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"\b(?:sk|pk|ghp|gho|xox[abp])[-_][A-Za-z0-9_-]{16,}"), "[REDACTED_KEY]"),
    (re.compile(r"(?i)\b(password|passwd|pwd|secret|token|api[_-]?key)(\s*[=:]\s*)[^\s,;&\"']+"), r"\1\2[REDACTED]"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[REDACTED_CARD]"),
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b"), "[REDACTED_IP]"),
    (re.compile(r"(?<!\w)\+?\d{1,3}[ .-]?\(?\d{2,4}\)?[ .-]?\d{3}[ .-]?\d{4}\b"), "[REDACTED_PHONE]"),
]


def redact(value):
    """Redact strings; recurse through dicts, lists and tuples; leave other types untouched."""
    if isinstance(value, str):
        for pattern, replacement in _PATTERNS:
            value = pattern.sub(replacement, value)
        return value
    if isinstance(value, dict):
        return {redact(key): ("[REDACTED]" if re.search(r"password|secret|token|api.?key|authorization|cookie|name|address", str(key), re.I) else redact(item)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(redact(item) for item in value)
    return value


def private_trace_mask(*, data, **kwargs):
    """Do not export arbitrary prompts, outputs, or metadata, including unrecognized PII."""
    return "[CONTENT OMITTED FOR PRIVACY]"


def _sanitize_record(record):
    from .config import settings

    record.msg = ("[CONTENT OMITTED FOR PRIVACY]" if settings.decision_support_only
                  else redact(record.getMessage()))
    record.args = None
    if record.exc_info:
        record.msg += " [exception details omitted]"
        record.exc_info = None
        record.exc_text = None
    record.stack_info = None
    for key in record.__dict__:
        if key not in _STANDARD_RECORD_FIELDS:
            record.__dict__[key] = "[CONTENT OMITTED FOR PRIVACY]"
    return record


def install_log_redaction():
    """Wrap the log record factory so every record is redacted regardless of handler or logger."""
    current = logging.getLogRecordFactory()
    if getattr(current, "_guardian_redacting", False):
        return

    def factory(*args, **kwargs):
        record = current(*args, **kwargs)
        return _sanitize_record(record)

    factory._guardian_redacting = True
    logging.setLogRecordFactory(factory)
    # `extra` is attached after the factory runs; cover JSON logging handlers too.
    original = logging.Logger.makeRecord
    if getattr(original, "_guardian_redacting", False):
        return

    def make_record(self, *args, **kwargs):
        record = original(self, *args, **kwargs)
        return _sanitize_record(record)
    make_record._guardian_redacting = True
    logging.Logger.makeRecord = make_record
    original_make_log_record = logging.makeLogRecord
    if not getattr(original_make_log_record, "_guardian_redacting", False):
        def make_log_record(attributes):
            return _sanitize_record(original_make_log_record(attributes))
        make_log_record._guardian_redacting = True
        logging.makeLogRecord = make_log_record
