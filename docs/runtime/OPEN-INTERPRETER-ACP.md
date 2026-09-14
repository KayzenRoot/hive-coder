# Open Interpreter ACP bridge

Pinned runtime: Open Interpreter `0.0.43`, ACP v1 over NDJSON JSON-RPC on stdio.

Lifecycle implemented by Hive:
1. exact binary-version preflight;
2. launch `interpreter acp` without a shell;
3. send `initialize` with ACP protocol version `1` and empty client capabilities;
4. validate returned protocol version, agent identity and capabilities;
5. optionally create a session using `session/new` with an absolute workspace path and no MCP servers;
6. receive `session/update` notifications;
7. send `session/cancel` as a notification when requested;
8. close a known session with `session/close`;
9. close stdin and terminate/kill only if bounded graceful shutdown fails.

No `session/prompt` API is exposed in HCODER-WO-0003, so this increment does not require provider credentials and does not execute model work.
