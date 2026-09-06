# DeepEval quality evaluation

Runtime validation and offline AI evaluation are intentionally separate.

- **Validation Agent** decides whether current evidence is sufficient to continue the operational workflow.
- **DeepEval** measures answer quality such as faithfulness, relevance, context relevance and tool/task correctness.

`test_rca_deepeval.py` is an optional live-model evaluation example. It requires a configured model/API key. The backend also returns deterministic demo evaluation scores when no judge model is available.
