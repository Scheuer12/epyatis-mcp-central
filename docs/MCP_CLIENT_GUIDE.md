# MCP client guide

The custom transport currently exposes:

- `POST /mcp/{instance}` for JSON-RPC initialize and subsequent requests;
- `GET|POST /mcp/{instance}/sse` for the legacy SSE path;
- `POST /mcp/{instance}/messages` for legacy messages.

Every request requires `Authorization: Bearer <instance-token>`. Do not add `token` to the query string. Initialization returns an `mcp-session-id`; send that header on subsequent requests for the same instance and bearer identity. Sessions expire after one hour and are not durable across process restarts.

Example initialization:

```bash
curl -i http://127.0.0.1:8000/mcp/demo-suite \
  -H "Authorization: Bearer $EPYATIS_INSTANCE_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}'
```

Named-client compatibility has not been certified. Validate protocol version, session behavior, reconnects, cancellation, errors, and tool results in an isolated environment before relying on a client.
