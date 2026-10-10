# Retrieval, tool usage, memory and adaptation proof
_Generated 2026-10-03 11:32:54_

## Tool usage (agent trace of one run)
| Agent / tool | Summary |
|---|---|
| orchestrator | Intent=runtime_incident; dynamic plan=['kubernetes', 'monitoring', 'change', 'rag', 'history', 'rca', 'validation'] |
| kubernetes | Pods are restarting and Kubernetes reports OOMKilled. |
| monitoring | 5xx and p95 latency increased immediately after deployment. |
| change | Memory limit changed from 1Gi to 128Mi. |
| rag | OOMKilled runbook recommends rollback/restoring validated memory limits. |
| history | Retrieved 3 labeled synthetic incident precedents. |
| rca | The latest checkout-api deployment reduced the container memory limit from 1Gi to 128Mi. The new limit is below application demand, causing OOMKilled  |
| validation | Evidence and confidence satisfy policy. |
| adaptive | accept_diagnosis |
| notification | Approval created; email notification attempted. |

## Retrieval (historical cases via RAG)
| Case | Service | Title |
|---|---|---|
| SYN-K8S-001 | checkout-api | Memory reduction caused OOMKilled pods |
| SYN-K8S-002 | checkout-api | CPU throttling saturated request workers |
| SYN-APP-010 | checkout-api | Rate-limit policy rejected legitimate traffic |

## Memory
Stored investigations before this run: 50; after: 50. Run `INV-0A6BF69E` was persisted and is retrievable via `GET /api/investigations/{id}`.

## Adaptation
| Validation | Adaptive action |
|---|---|
| {"is_sufficient": true, "reason": "Evidence and confidence satisfy policy."} | `accept_diagnosis` |

Live mode adapts by declining to claim a cause when evidence is thin:
- live status `insufficient_data`, confidence 0.0, action `collect_evidence` (no unsupported remediation).
