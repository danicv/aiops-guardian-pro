"""Optional DeepEval example. Run only when a supported judge model/API key is configured."""
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase

QUESTION = "Why did checkout-api fail after the deployment?"
ANSWER = "The deployment reduced the memory limit from 1Gi to 128Mi, causing OOMKilled restarts and elevated 5xx errors."
CONTEXT = [
    "Deployment diff: memory limit 1Gi -> 128Mi.",
    "Kubernetes event: OOMKilled.",
    "HTTP 5xx increased immediately after deployment."
]

def test_rca_quality():
    case = LLMTestCase(input=QUESTION, actual_output=ANSWER, retrieval_context=CONTEXT)
    assert_test(case, [AnswerRelevancyMetric(threshold=0.7), FaithfulnessMetric(threshold=0.7)])
