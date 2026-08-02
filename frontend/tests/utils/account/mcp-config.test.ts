import { describe, expect, it } from "vitest";

import {
  API_KEY_PLACEHOLDER,
  buildClaudeCodeCommand,
  buildCursorConfig,
  buildMcpConfig,
  buildVsCodeConfig,
  MCP_HOSTS,
  MCP_SERVER_NAME,
} from "@utils/account/mcp-config";

const URL = "https://real-estate-consultant-mcp.vercel.app/mcp";
const KEY = "rad_abcdefghijklmnop";

describe("buildCursorConfig", () => {
  it("nests the server under mcpServers with a bearer header", () => {
    const parsed = JSON.parse(buildCursorConfig(URL, KEY));
    expect(parsed.mcpServers[MCP_SERVER_NAME]).toEqual({
      url: URL,
      headers: { Authorization: `Bearer ${KEY}` },
    });
  });

  it("emits valid, indented JSON", () => {
    const out = buildCursorConfig(URL, KEY);
    expect(() => JSON.parse(out)).not.toThrow();
    expect(out).toContain("\n  ");
  });
});

describe("buildVsCodeConfig", () => {
  it("nests under servers with an explicit http type", () => {
    const parsed = JSON.parse(buildVsCodeConfig(URL, KEY));
    expect(parsed.servers[MCP_SERVER_NAME]).toEqual({
      type: "http",
      url: URL,
      headers: { Authorization: `Bearer ${KEY}` },
    });
  });

  it("does not use the Cursor mcpServers key", () => {
    expect(JSON.parse(buildVsCodeConfig(URL, KEY)).mcpServers).toBeUndefined();
  });
});

describe("buildClaudeCodeCommand", () => {
  it("builds an http transport add command carrying the key", () => {
    const out = buildClaudeCodeCommand(URL, KEY);
    expect(out).toContain("claude mcp add --transport http");
    expect(out).toContain(MCP_SERVER_NAME);
    expect(out).toContain(URL);
    expect(out).toContain(`Authorization: Bearer ${KEY}`);
  });

  it("quotes the header so the shell keeps it as one argument", () => {
    expect(buildClaudeCodeCommand(URL, KEY)).toContain(`--header "Authorization: Bearer ${KEY}"`);
  });
});

describe("buildMcpConfig", () => {
  it("dispatches to the matching builder for every listed host", () => {
    for (const host of MCP_HOSTS) {
      expect(buildMcpConfig(host.id, URL, KEY)).toBe(
        host.id === "cursor"
          ? buildCursorConfig(URL, KEY)
          : host.id === "claude-code"
            ? buildClaudeCodeCommand(URL, KEY)
            : buildVsCodeConfig(URL, KEY),
      );
    }
  });

  it("interpolates the key for every host", () => {
    for (const host of MCP_HOSTS) {
      expect(buildMcpConfig(host.id, URL, KEY)).toContain(KEY);
    }
  });

  it("carries the placeholder through when the plaintext key is gone", () => {
    for (const host of MCP_HOSTS) {
      const out = buildMcpConfig(host.id, URL, API_KEY_PLACEHOLDER);
      expect(out).toContain(API_KEY_PLACEHOLDER);
      expect(out).not.toContain(KEY);
    }
  });
});
