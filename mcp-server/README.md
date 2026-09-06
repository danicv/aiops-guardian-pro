# DevOps MCP Server

`server.py` exposes diagnostic and action tools using FastMCP. `http_bridge.py` exists only to make the local Docker demo easy to inspect through Swagger.

For production, split the service into **read MCP** and **action MCP** identities. The action server must require authenticated caller identity, guardrail/policy validation, and approval state before any mutation.
