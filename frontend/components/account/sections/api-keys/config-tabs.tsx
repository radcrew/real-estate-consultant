"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@components/ui/button-variants";
import { MCP_SERVER_URL } from "@config/env";
import { buildMcpConfig, MCP_HOSTS, type McpHost } from "@utils/account/mcp-config";
import { cn } from "@utils/common";

export type McpConfigTabsProps = {
  /** Plaintext key when available, otherwise API_KEY_PLACEHOLDER. */
  apiKey: string;
  url?: string;
};

/**
 * Host-specific setup snippet. Shared by the created-key dialog (real key) and
 * the section's connect panel (placeholder), so the two can never drift.
 */
export const McpConfigTabs = ({ apiKey, url = MCP_SERVER_URL }: McpConfigTabsProps) => {
  const [host, setHost] = useState<McpHost>("cursor");
  const [copied, setCopied] = useState(false);

  const snippet = buildMcpConfig(host, url, apiKey);

  const selectHost = (next: McpHost) => {
    setHost(next);
    setCopied(false);
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(snippet);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <div>
      <div className="flex gap-1" role="tablist" aria-label="AI host">
        {MCP_HOSTS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={host === id}
            onClick={() => selectHost(id)}
            className={cn(
              "cursor-pointer rounded-lg px-3 py-1.5 text-sm transition-colors",
              host === id
                ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900"
                : "text-muted-foreground hover:bg-neutral-100 dark:hover:bg-neutral-800",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="relative mt-2">
        <pre
          data-testid="mcp-config-snippet"
          className="overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-50 p-3 pr-24 font-mono text-xs dark:border-neutral-700 dark:bg-neutral-900"
        >
          {snippet}
        </pre>
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopy}
          aria-label={copied ? "Config copied" : "Copy config"}
          className="absolute right-2 top-2"
        >
          {copied ? <Check aria-hidden /> : <Copy aria-hidden />}
          {copied ? "Copied" : "Copy"}
        </Button>
      </div>
    </div>
  );
};
