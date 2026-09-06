# Operations guide

Health checks:
- Backend: `GET /api/healthz`
- MCP bridge: `GET /healthz`

Useful local commands:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mcp-server
docker compose exec postgres psql -U guardian -d guardian
```

Mailpit: http://localhost:8025
Grafana: http://localhost:3001

Operational philosophy: **diagnose -> correlate -> validate -> classify risk -> approve -> execute -> verify -> audit**.
