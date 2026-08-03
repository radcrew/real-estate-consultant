/**
 * MCP client config snippets for the "connect an AI tool" flow.
 *
 * Pure string builders — no React, no env reads — so the caller decides which
 * URL and key to interpolate and these stay trivially testable. Shapes match
 * `services/mcp/README.md` ("Cursor host config (remote / Vercel)").
 */

export const MCP_SERVER_NAME = "radestate";

/** Shown in place of a real key when the plaintext is no longer available. */
export const API_KEY_PLACEHOLDER = "rad_your_key_here";

export type McpHost = "cursor" | "claude-code" | "vscode";

export const MCP_HOSTS: { id: McpHost; label: string; language: string }[] = [
  { id: "cursor", label: "Cursor", language: "json" },
  { id: "claude-code", label: "Claude Code", language: "bash" },
  { id: "vscode", label: "VS Code", language: "json" },
];

/** `.cursor/mcp.json` — remote Streamable HTTP with a bearer header. */
export const buildCursorConfig = (url: string, apiKey: string): string =>
  JSON.stringify(
    {
      mcpServers: {
        [MCP_SERVER_NAME]: {
          url,
          headers: { Authorization: `Bearer ${apiKey}` },
        },
      },
    },
    null,
    2,
  );

/** `claude mcp add` — the CLI writes the host config itself. */
export const buildClaudeCodeCommand = (url: string, apiKey: string): string =>
  [
    "claude mcp add --transport http",
    MCP_SERVER_NAME,
    url,
    `--header "Authorization: Bearer ${apiKey}"`,
  ].join(" ");

/** `.vscode/mcp.json` — VS Code nests under `servers`, not `mcpServers`. */
export const buildVsCodeConfig = (url: string, apiKey: string): string =>
  JSON.stringify(
    {
      servers: {
        [MCP_SERVER_NAME]: {
          type: "http",
          url,
          headers: { Authorization: `Bearer ${apiKey}` },
        },
      },
    },
    null,
    2,
  );

export const buildMcpConfig = (host: McpHost, url: string, apiKey: string): string => {
  switch (host) {
    case "cursor":
      return buildCursorConfig(url, apiKey);
    case "claude-code":
      return buildClaudeCodeCommand(url, apiKey);
    case "vscode":
      return buildVsCodeConfig(url, apiKey);
  }
};
