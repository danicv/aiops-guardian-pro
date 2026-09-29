# Operational knowledge
This directory is the seed corpus for the RAG layer: runbooks, SOPs, architecture notes, known errors and previous RCAs.

For local SRE training, the application also includes a structured PostgreSQL
case library of 34 fictional incidents spanning application latency/errors,
Kubernetes, databases, queues, networking, CI/CD, deployments, security, and
observability. Seed it from the Simulator screen or use the demo-only
`POST /api/demo/cases/seed` endpoint. These cases are labeled synthetic and are
retrieved as historical analogies, never as evidence about the current service.
Production/demo seeding is disabled unless `DEMO_DATA_ENABLED=true` is set.

Production ingestion should chunk approved content, attach tenant/source metadata, generate embeddings, persist to FAISS or an enterprise vector store, enforce document authorization, and return source citations with retrieved evidence.
