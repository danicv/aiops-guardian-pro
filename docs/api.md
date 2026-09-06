# API summary

Swagger UI: `/docs`

## Start investigation
`POST /api/investigations`

```json
{"query":"Why is checkout-api failing after today's deployment?","application":"checkout-api","environment":"prod","namespace":"default"}
```

## Release risk
`POST /api/release-risk`

```json
{"application":"checkout-api","environment":"prod","version":"v2.0.0","previous_version":"v1.9.0","changes":{"memory_after":"128Mi"}}
```

## Approvals
- `GET /api/approvals`
- `POST /api/approvals/{id}/approve`
- `POST /api/approvals/{id}/reject`

## Integrations
- `GET /api/integrations/providers`
- `GET /api/integrations`
- `POST /api/integrations`
- `POST /api/integrations/test`

## Email
- `POST /api/notifications/email`
