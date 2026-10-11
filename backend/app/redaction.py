"""Redact personal and secret data before it reaches logs or audit records."""
import logging
import re

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
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(redact(item) for item in value)
    return value


def install_log_redaction():
    """Wrap the log record factory so every record is redacted regardless of handler or logger."""
    current = logging.getLogRecordFactory()
    if getattr(current, "_guardian_redacting", False):
        return

    def factory(*args, **kwargs):
        record = current(*args, **kwargs)
        record.msg = redact(record.getMessage())
        record.args = None
        return record

    factory._guardian_redacting = True
    logging.setLogRecordFactory(factory)
