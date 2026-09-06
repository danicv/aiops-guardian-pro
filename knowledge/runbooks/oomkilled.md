# Kubernetes OOMKilled Recovery Procedure

## Symptoms
- pod termination reason `OOMKilled`
- rising restart count
- elevated error rate and latency
- memory working set approaches the configured limit

## Investigation
1. Check the most recent deployment and resource changes.
2. Compare current memory limit with historical peak and normal working set.
3. Review whether performance/load testing covered the new configuration.
4. Check for memory leaks and traffic changes.
5. Correlate incident start time with release time.

## Safe remediation
When the incident clearly correlates with an unsafe resource-limit reduction, roll back to the last known-good release or restore the previous validated memory limit. Production remediation must follow approval policy.

## Verification
- desired replicas healthy
- OOMKilled stops
- restart rate returns to baseline
- HTTP 5xx returns to baseline
- p95 latency returns to baseline
