# Agent catalog

## Orchestrator Agent
Classifies intent, builds an investigation plan, selects specialized agents, maintains shared state, controls retries/loops, pauses for approval, resumes execution, and determines when the goal is complete.

## Pipeline Agent
Reads pipeline status, failed stages, build logs, test results, security/IaC outcomes, and deployment metadata.

## Change Agent
Compares releases, commits, Kubernetes resource values, configuration, environment variables, and infrastructure changes.

## Kubernetes Agent
Inspects pods, deployments, events, logs, readiness, restarts, OOMKilled and resource status.

## Monitoring Agent
Analyzes CPU, memory, HTTP 4xx/5xx, latency, restart rate, DB metrics, logs and traces.

## RAG Agent
Retrieves approved runbooks, SOPs, architecture documents, known errors and previous RCA documents.

## History Agent
Queries structured incident, release, approval and remediation history from PostgreSQL.

## Correlation / RCA Agent
Synthesizes independent evidence into an evidence-backed probable root cause and recommended next action.

## Validation Agent
Checks confidence and evidence sufficiency before remediation.

## Adaptive Agent
When evidence is insufficient, chooses the next evidence source or investigation step rather than blindly continuing a static flow.

## Release Risk Agent
Scores pre-deployment risk using change severity, test evidence, historical incidents, blast radius and rollback readiness.

## Remediation Agent
Proposes a corrective action but cannot bypass platform guardrails.

## Verification Agent
Validates post-remediation service health against baseline.

## DeepEval
Evaluation framework for response relevance, faithfulness, context relevance, and tool/task quality. It is not a runtime orchestrator.
