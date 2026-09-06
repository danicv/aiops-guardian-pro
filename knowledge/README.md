# Operational knowledge
This directory is the seed corpus for the RAG layer: runbooks, SOPs, architecture notes, known errors and previous RCAs.

Production ingestion should chunk approved content, attach tenant/source metadata, generate embeddings, persist to FAISS or an enterprise vector store, enforce document authorization, and return source citations with retrieved evidence.
