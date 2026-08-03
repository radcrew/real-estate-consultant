"use client";

import { Plug, RefreshCw, Trash2 } from "lucide-react";

import { Button } from "@components/ui/button-variants";
import type { McpApiKey } from "@services/account";
import { API_KEY_PLACEHOLDER } from "@utils/account/mcp-config";
import { API_KEY_EXPIRY_WARNING_DAYS } from "@utils/account/validation";

import { AccountField } from "../../field";
import { ACCOUNT_SECTION_CARD_CLASS } from "../../styles";
import { McpConfigTabs } from "./config-tabs";

/**
 * Scopes offered in the UI. `mcp:admin` is deliberately omitted — the MCP
 * server no longer registers admin tools, so offering the scope would
 * advertise capability that does not exist.
 */
export const SCOPE_OPTIONS = [
  { value: "*", label: "Full access", hint: "Read and write" },
  { value: "mcp:read", label: "Read only", hint: "Search and view listings" },
  { value: "mcp:write", label: "Read and write", hint: "Also create outreach drafts" },
] as const;

export type AccountApiKeysSectionProps = {
  keys: McpApiKey[];
  loading: boolean;
  loadError: string | null;
  name: string;
  scope: string;
  expiresInDays: string;
  errors: Partial<Record<string, string>>;
  creating: boolean;
  revokingId: string | null;
  confirmingRevokeId: string | null;
  rotatingId: string | null;
  /** Key that has just been replaced and is waiting to be revoked. */
  replacedKeyId: string | null;
  onChangeName: (value: string) => void;
  onChangeScope: (value: string) => void;
  onChangeExpiresInDays: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  onRotate: (key: McpApiKey) => void;
  onRequestRevoke: (key: McpApiKey) => void;
  onConfirmRevoke: (key: McpApiKey) => void;
  onCancelRevoke: () => void;
};

const isRevoked = (key: McpApiKey) => Boolean(key.revoked_at);

const isExpired = (key: McpApiKey) =>
  Boolean(key.expires_at) && new Date(String(key.expires_at)).getTime() < Date.now();

/** Whole days until expiry, or null when the key never expires or the date is unusable. */
const daysUntilExpiry = (key: McpApiKey): number | null => {
  if (!key.expires_at) return null;
  const at = new Date(String(key.expires_at)).getTime();
  if (Number.isNaN(at)) return null;
  return Math.ceil((at - Date.now()) / 86_400_000);
};

const formatDate = (value: string | null) => {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleDateString();
};

const KeyRow = ({
  apiKey,
  revoking,
  confirming,
  rotating,
  replaced,
  onRotate,
  onRequestRevoke,
  onConfirmRevoke,
  onCancelRevoke,
}: {
  apiKey: McpApiKey;
  revoking: boolean;
  confirming: boolean;
  rotating: boolean;
  replaced: boolean;
  onRotate: (key: McpApiKey) => void;
  onRequestRevoke: (key: McpApiKey) => void;
  onConfirmRevoke: (key: McpApiKey) => void;
  onCancelRevoke: () => void;
}) => {
  const expired = isExpired(apiKey);
  const daysLeft = daysUntilExpiry(apiKey);
  const expiringSoon =
    !expired && daysLeft !== null && daysLeft <= API_KEY_EXPIRY_WARNING_DAYS;

  return (
    <li
      className={
        expired
          ? "flex flex-wrap items-center gap-x-4 gap-y-1 py-4 opacity-60"
          : "flex flex-wrap items-center gap-x-4 gap-y-1 py-4"
      }
      data-testid="api-key-row"
      data-inactive={expired ? "true" : undefined}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-foreground">{apiKey.name}</span>
          {expired ? (
            <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-700 dark:bg-neutral-700 dark:text-neutral-200">
              Expired
            </span>
          ) : null}
          {expiringSoon ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900 dark:bg-amber-950/60 dark:text-amber-200">
              {daysLeft !== null && daysLeft <= 0
                ? "Expires today"
                : `Expires in ${daysLeft} day${daysLeft === 1 ? "" : "s"}`}
            </span>
          ) : null}
          {replaced && !expired ? (
            <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-900 dark:bg-amber-950/60 dark:text-amber-200">
              Replaced — still active
            </span>
          ) : null}
        </div>
        <p className="mt-0.5 font-mono text-xs text-muted-foreground">{apiKey.key_prefix}…</p>
      </div>

      <dl className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-muted-foreground">
        <div>
          <dt className="inline">Scopes: </dt>
          <dd className="inline font-mono">{apiKey.scopes.join(", ")}</dd>
        </div>
        <div>
          <dt className="inline">Created: </dt>
          <dd className="inline">{formatDate(apiKey.created_at)}</dd>
        </div>
        <div>
          <dt className="inline">Last used: </dt>
          <dd className="inline">{apiKey.last_used_at ? formatDate(apiKey.last_used_at) : "Never"}</dd>
        </div>
        <div>
          <dt className="inline">Expires: </dt>
          <dd className="inline">{formatDate(apiKey.expires_at)}</dd>
        </div>
      </dl>

      {confirming ? (
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Revoke permanently?</span>
          <Button
            variant="destructive"
            size="sm"
            disabled={revoking}
            onClick={() => onConfirmRevoke(apiKey)}
            aria-label={`Confirm revoking ${apiKey.name}`}
          >
            {revoking ? "Revoking…" : "Confirm"}
          </Button>
          <Button variant="ghost" size="sm" disabled={revoking} onClick={onCancelRevoke}>
            Cancel
          </Button>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={rotating}
            onClick={() => onRotate(apiKey)}
            aria-label={`Rotate ${apiKey.name}`}
          >
            <RefreshCw aria-hidden />
            {rotating ? "Rotating…" : "Rotate"}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => onRequestRevoke(apiKey)}
            aria-label={`Revoke ${apiKey.name}`}
          >
            <Trash2 aria-hidden />
            Revoke
          </Button>
        </div>
      )}
    </li>
  );
};

export const AccountApiKeysSection = ({
  keys,
  loading,
  loadError,
  name,
  scope,
  expiresInDays,
  errors,
  creating,
  revokingId,
  confirmingRevokeId,
  rotatingId,
  replacedKeyId,
  onChangeName,
  onChangeScope,
  onChangeExpiresInDays,
  onSubmit,
  onRotate,
  onRequestRevoke,
  onConfirmRevoke,
  onCancelRevoke,
}: AccountApiKeysSectionProps) => {
  // A revoked key is a dead credential: it cannot be rotated, revoked again or
  // used, so listing it is noise that only makes the live keys harder to find.
  // The API still returns them, so drop them here.
  const visibleKeys = keys.filter((apiKey) => !isRevoked(apiKey));

  return (
    <section className={ACCOUNT_SECTION_CARD_CLASS} aria-label="MCP API keys">
      <form onSubmit={onSubmit} className="flex flex-col gap-5">
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <AccountField
            id="api-key-name"
            label="Key name"
            value={name}
            onChange={onChangeName}
            error={errors.name}
            autoComplete="off"
          />

          <div className="flex flex-col gap-1.5">
            <label htmlFor="api-key-scope" className="text-sm font-medium text-foreground">
              Access
            </label>
            <select
              id="api-key-scope"
              value={scope}
              onChange={(e) => onChangeScope(e.target.value)}
              className="h-10 rounded-lg border border-neutral-200 bg-white px-3 text-sm text-foreground dark:border-neutral-700 dark:bg-neutral-900"
            >
              {SCOPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label} — {option.hint}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <AccountField
              id="api-key-expires"
              label="Expires in (days)"
              type="number"
              value={expiresInDays}
              onChange={onChangeExpiresInDays}
              error={errors.expiresInDays}
              autoComplete="off"
            />
            <p className="text-xs text-muted-foreground">
              Short-lived keys limit the damage if one leaks. Clear this field for a key that never
              expires.
            </p>
          </div>
        </div>

        {errors.form ? (
          <p className="text-sm text-destructive" role="alert">
            {errors.form}
          </p>
        ) : null}

        <div className="pt-1">
          <Button type="submit" disabled={creating}>
            <Plug aria-hidden />
            {creating ? "Creating…" : "Create key"}
          </Button>
        </div>
      </form>

      <div className="mt-8 border-t border-border pt-6">
        <h3 className="text-sm font-semibold text-foreground">Your keys</h3>

        {replacedKeyId ? (
          <p
            className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200"
            role="status"
          >
            A replacement key was created. Update your AI tool config with the new key first — the
            old key keeps working until you revoke it.
          </p>
        ) : null}

        {loadError ? (
          <p className="mt-3 text-sm text-destructive" role="alert">
            {loadError}
          </p>
        ) : null}

        {loading ? <p className="mt-3 text-sm text-muted-foreground">Loading keys…</p> : null}

        {!loading && !loadError && visibleKeys.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">
            You have no API keys yet. Create one above to connect an AI tool.
          </p>
        ) : null}

        {visibleKeys.length > 0 ? (
          <ul className="mt-2 divide-y divide-border">
            {visibleKeys.map((apiKey) => (
              <KeyRow
                key={apiKey.id}
                apiKey={apiKey}
                revoking={revokingId === apiKey.id}
                confirming={confirmingRevokeId === apiKey.id}
                rotating={rotatingId === apiKey.id}
                replaced={replacedKeyId === apiKey.id}
                onRotate={onRotate}
                onRequestRevoke={onRequestRevoke}
                onConfirmRevoke={onConfirmRevoke}
                onCancelRevoke={onCancelRevoke}
              />
            ))}
          </ul>
        ) : null}
      </div>

      {visibleKeys.length > 0 ? (
        <div className="mt-8 border-t border-border pt-6">
          <h3 className="text-sm font-semibold text-foreground">Connect an AI tool</h3>
          <p className="mt-1 mb-3 text-sm text-muted-foreground">
            Paste this into your host config, replacing{" "}
            <code className="font-mono text-xs">{API_KEY_PLACEHOLDER}</code> with a key you saved
            when you created it. Keys cannot be shown again.
          </p>
          <McpConfigTabs apiKey={API_KEY_PLACEHOLDER} />
        </div>
      ) : null}
    </section>
  );
};
