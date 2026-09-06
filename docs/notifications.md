# Notifications

The project implements a generic Notification Service with SMTP email as the first channel. The interface can be extended to Teams, Slack, PagerDuty, ServiceNow or approved SMS providers.

## Events
- pipeline failure
- high-risk release
- incident created
- RCA completed
- approval requested
- approval approved/rejected
- remediation started/failed
- recovery verification completed

## Approval email
The email contains application/environment, investigation ID, probable cause summary, risk, recommended action and a **Review & Approve** portal link. Authentication and authorization happen in the application, not through an email reply.
