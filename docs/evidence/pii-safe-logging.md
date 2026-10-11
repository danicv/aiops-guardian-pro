# PII-safe logging evidence
_Generated 2026-10-10 21:52:16_

Input contained synthetic values for an email, IP address, phone number, card number, password and bearer token (raw values are intentionally not reproduced here).

Log line written to disk:

```
WARNING user request: Investigating for [REDACTED_EMAIL] from [REDACTED_IP], call [REDACTED_PHONE], card [REDACTED_CARD], password=[REDACTED], Authorization: Bearer [REDACTED_TOKEN]
```

Audit record payload stored in the database:

```
{"comment": "Investigating for [REDACTED_EMAIL] from [REDACTED_IP], call [REDACTED_PHONE], card [REDACTED_CARD], password=[REDACTED], Authorization: Bearer [REDACTED_TOKEN]"}
```

Sensitive values found in either: **none**.
