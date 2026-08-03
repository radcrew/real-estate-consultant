"use client";

import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from "@headlessui/react";
import { AlertTriangle, Check, Copy } from "lucide-react";
import { useState } from "react";

import { Button } from "@components/ui/button-variants";
import type { McpApiKeyCreated } from "@services/account";

import { McpConfigTabs } from "./config-tabs";

export type ApiKeyCreatedDialogProps = {
  apiKey: McpApiKeyCreated | null;
  onDismiss: () => void;
};

/**
 * One-shot reveal for a newly created key.
 *
 * The plaintext `rad_…` exists only in the create response — the list endpoint
 * returns `key_prefix` and never the key itself. So this dialog is the single
 * moment the user can capture it, and dismissal is gated on an explicit
 * acknowledgement: `onClose` is a no-op until the box is ticked, which also
 * disables Esc and backdrop-click.
 */
export const ApiKeyCreatedDialog = ({ apiKey, onDismiss }: ApiKeyCreatedDialogProps) => {
  const [acknowledged, setAcknowledged] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleDismiss = () => {
    setAcknowledged(false);
    setCopied(false);
    onDismiss();
  };

  const handleCopy = async () => {
    if (!apiKey) return;
    try {
      await navigator.clipboard.writeText(apiKey.api_key);
      setCopied(true);
    } catch {
      // Clipboard can be unavailable (insecure origin, denied permission).
      // The key is selectable in the DOM, so manual copy still works.
      setCopied(false);
    }
  };

  return (
    <Dialog
      open={Boolean(apiKey)}
      onClose={acknowledged ? handleDismiss : () => {}}
      className="relative z-50"
    >
      <DialogBackdrop className="fixed inset-0 bg-neutral-900/50 dark:bg-black/80" />
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <DialogPanel className="w-full max-w-xl rounded-2xl border border-black/5 bg-white p-6 text-left text-neutral-900 shadow-xl dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-200">
            <DialogTitle as="h3" className="text-lg font-semibold">
              Copy your API key
            </DialogTitle>

            <div
              className="mt-4 flex gap-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200"
              role="alert"
            >
              <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
              <p>
                This is the only time this key will be shown. Store it somewhere safe — if you lose
                it you will need to revoke this key and create a new one.
              </p>
            </div>

            <div className="mt-4 flex items-center gap-2">
              <code
                data-testid="api-key-plaintext"
                className="min-w-0 flex-1 overflow-x-auto rounded-lg border border-neutral-200 bg-neutral-50 px-3 py-2 font-mono text-sm dark:border-neutral-700 dark:bg-neutral-900"
              >
                {apiKey?.api_key}
              </code>
              <Button
                variant="outline"
                onClick={handleCopy}
                aria-label={copied ? "API key copied" : "Copy API key"}
              >
                {copied ? <Check aria-hidden /> : <Copy aria-hidden />}
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>

            <p className="mt-3 text-xs text-muted-foreground">
              {apiKey?.name} · {apiKey?.scopes.join(", ")}
            </p>

            <div className="mt-5 border-t border-neutral-200 pt-5 dark:border-neutral-700">
              <h4 className="text-sm font-medium">Add it to your AI tool</h4>
              {apiKey ? <McpConfigTabs apiKey={apiKey.api_key} /> : null}
            </div>

            <label className="mt-5 flex items-start gap-2 text-sm">
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
                className="mt-0.5 size-4 rounded border-neutral-300 text-primary-500 focus:ring-primary-500 dark:bg-neutral-700"
              />
              <span>I have saved this key somewhere safe</span>
            </label>

            <div className="mt-5 flex justify-end">
              <Button onClick={handleDismiss} disabled={!acknowledged}>
                Done
              </Button>
            </div>
          </DialogPanel>
        </div>
      </div>
    </Dialog>
  );
};
