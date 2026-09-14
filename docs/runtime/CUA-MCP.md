# Cua Driver MCP bridge

Pinned runtime: Cua Driver `0.28.1`. Hive uses the modern stdio MCP revision `2026-07-28` documented by that exact release.

Lifecycle implemented by Hive:
1. exact binary-version preflight;
2. launch `cua-driver mcp` without a shell and disable Cua telemetry in the production constructor;
3. send only `server/discover` with per-request protocol and client-capability metadata;
4. require `resultType=complete`, the pinned modern protocol in `supportedVersions`, capabilities object and well-formed tool metadata;
5. record server identity and tool names as inventory;
6. shut down the stdio process through the bounded process lifecycle.

The adapter has no `tools/call` method. Tool names are inventory only, not authorization. Real screen/mouse/keyboard/window/browser actions remain forbidden until a later HIGH_ASSURANCE Work Order proves the permission and emergency-control model.
