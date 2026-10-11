# Embedding retrieval evidence
_Generated 2026-10-10 21:52:16; embeddings `nomic-embed-text` via Ollama; 34-case library; similarity floor 0.55_

## 1. Lexical vs embedding top-1 (8 paraphrased queries that reuse none of the library's wording)

| Query | Expected | Lexical top-1 | Embedding top-1 (cosine) |
|---|---|---|---|
| Containers are being terminated for using more RAM than allowed since the last release | SYN-K8S-001 | SYN-K8S-002 ❌ | SYN-K8S-001 (0.7229) ✅ |
| Everything is slow because requests queue waiting for a free handle to the data store | SYN-APP-001 | SYN-APP-001 ✅ | SYN-APP-001 (0.6895) ✅ |
| Calls to our partner started failing because a security document lapsed | SYN-NET-002 | SYN-NET-002 ✅ | SYN-NET-002 (0.6423) ✅ |
| A single bad record keeps getting reprocessed and nothing behind it moves | SYN-QUEUE-002 | SYN-APP-010 ❌ | SYN-DB-003 (0.602) ❌ |
| Monitoring graph went flat and we assumed errors stopped, but the target vanished | SYN-OBS-001 | SYN-K8S-004 ❌ | SYN-OBS-001 (0.6703) ✅ |
| Pods keep getting killed by the health check before the app finishes booting | SYN-K8S-003 | SYN-K8S-001 ❌ | SYN-K8S-003 (0.6847) ✅ |
| Our login to the database stopped working after credentials were changed | SYN-DEPLOY-002 | SYN-DEPLOY-002 ✅ | SYN-DEPLOY-002 (0.6035) ✅ |
| Users behind the office network are all getting blocked with 429 | SYN-APP-010 | SYN-APP-010 ✅ | SYN-APP-010 (0.6455) ✅ |

**Top-1 accuracy: lexical 4/8, embeddings 7/8.**

## 2. Missing information: queries with no relevant precedent

| Query | Lexical returns | Embeddings return |
|---|---|---|
| The marketing site hero image is blurry on mobile phones | SYN-CI-004 (irrelevant match) | nothing, below the similarity floor |
| What is the best pizza topping | SYN-DEPLOY-002 (irrelevant match) | nothing, below the similarity floor |

Embeddings let the agent say 'no precedent found' instead of presenting an unrelated case.

## 3. Answer quality with and without retrieval (qwen2.5:1.5b, temperature 0)

**Question:** Containers are being terminated for using more RAM than allowed since the last release

- Without retrieval: The containers are being terminated because they are using more RAM than the allowed limit.
- With retrieval (SYN-K8S-001): The root cause of the incident was a deployment that reduced the container limit below the observed working-set demand, leading to OOM (Out of Memory) kills.

**Question:** Everything is slow because requests queue waiting for a free handle to the data store

- Without retrieval: The cause is unconfirmed.
- With retrieval (SYN-APP-001): The cause is unconfirmed.

Caveat: the 1.5B local model is inconsistent in how it uses context (it can ignore it or state a past cause as fact). Retrieval is therefore also shown to the user as labelled synthetic precedents in the evidence panel; the answer text is not the proof of retrieval quality, section 1 is.
