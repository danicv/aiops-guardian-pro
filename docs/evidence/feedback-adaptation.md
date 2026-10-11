# Feedback adaptation evidence
_Generated 2026-10-10 21:52:04_

Query: `checkout-api pods keep restarting and are OOMKilled after the memory limit was lowered`

Feedback stores only a case id, an optional investigation id and a +1/-1 rating (no free text, so nothing personal is stored). Net votes are clamped to ±3 and scale a case's score by `1 + 0.15 × votes`.

## Before feedback

| Rank | Case | Score | Net votes |
|---|---|---|---|
| 1 | SYN-K8S-001 Memory reduction caused OOMKilled pods | 0.8579 | 0 |
| 2 | SYN-K8S-003 Liveness probe caused restart loop | 0.7823 | 0 |
| 3 | SYN-DEPLOY-001 Readiness gate never passed after config rollout | 0.7191 | 0 |
| 4 | SYN-NET-001 Cluster DNS lookup timeouts | 0.6966 | 0 |

Reviewers mark `SYN-K8S-001` not helpful 3 times.

## After feedback

| Rank | Case | Score | Net votes |
|---|---|---|---|
| 1 | SYN-K8S-003 Liveness probe caused restart loop | 0.7823 | 0 |
| 2 | SYN-DEPLOY-001 Readiness gate never passed after config rollout | 0.7191 | 0 |
| 3 | SYN-NET-001 Cluster DNS lookup timeouts | 0.6966 | 0 |
| 4 | SYN-K8S-002 CPU throttling saturated request workers | 0.6965 | 0 |

Reviewers mark `SYN-K8S-003` helpful 2 times.

## After positive feedback

| Rank | Case | Score | Net votes |
|---|---|---|---|
| 1 | SYN-K8S-003 Liveness probe caused restart loop | 1.017 | 2 |
| 2 | SYN-DEPLOY-001 Readiness gate never passed after config rollout | 0.7191 | 0 |
| 3 | SYN-NET-001 Cluster DNS lookup timeouts | 0.6966 | 0 |
| 4 | SYN-K8S-002 CPU throttling saturated request workers | 0.6965 | 0 |

`SYN-K8S-001` (net votes -3) is now ranked 34 of 34 candidates, down from 1.

## What changed and why

- Top-1 moved from `SYN-K8S-001` to `SYN-K8S-003` after negative feedback; ranking changes only the order of precedents.
- Limits: ratings are global, not per user or per service; clamping keeps a crowd of votes from hiding the best match; feedback never changes guardrail decisions, which stay deterministic.
