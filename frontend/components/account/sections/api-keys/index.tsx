"use client";

import { Plug, Trash2 } from "lucide-react";

import { Button } from "@components/ui/button-variants";
import type { McpApiKey } from "@services/account";

import { AccountField } from "../../field";
import { ACCOUNT_SECTION_CARD_CLASS } from "../../styles";

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
  onChangeName: (value: string) => void;
  onChangeScope: (value: string) => void;
  onChangeExpiresInDays: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  onRevoke: (key: McpApiKey) => void;
};

const isRevoked = (key: McpApiKey) => Boolean(key.revoked_at);

const isExpired = (key: McpApiKey) =>
  Boolean(key.expires_at) && new Date(String(key.expires_at)).getTime() < Date.now();

const formatDate = (value: string | null) => {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleDateString();
};

const KeyRow = ({
  apiKey,
  revoking,
  onRevoke,
}: {
  apiKey: McpApiKey;
  revoking: boolean;
  onRevoke: (key: McpApiKey) => void;
}) => {
  const revoked = isRevoked(apiKey);
  const expired = !revoked && isExpired(apiKey);
  const inactive = revoked || expired;

  return (
    <li
      className={
        inactive
          ? "flex flex-wrap items-center gap-x-4 gap-y-1 py-4 opacity-60"
          : "flex flex-wrap items-center gap-x-4 gap-y-1 py-4"
      }
      data-testid="api-key-row"
      data-inactive={inactive ? "true" : undefined}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium text-foreground">{apiKey.name}</span>
          {revoked ? (
            <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-700 dark:bg-neutral-700 dark:text-neutral-200">
              Revoked
            </span>
          ) : null}
          {expired ? (
            <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-xs text-neutral-700 dark:bg-neutral-700 dark:text-neutral-200">
              Expired
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

      {revoked ? null : (
        <Button
          variant="destructive"
          size="sm"
          disabled={revoking}
          onClick={() => onRevoke(apiKey)}
          aria-label={`Revoke ${apiKey.name}`}
        >
          <Trash2 aria-hidden />
          {revoking ? "Revoking…" : "Revoke"}
        </Button>
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
  onChangeName,
  onChangeScope,
  onChangeExpiresInDays,
  onSubmit,
  onRevoke,
}: AccountApiKeysSectionProps) => (
  <section className={ACCOUNT_SECTION_CARD_CLASS} aria-labelledby="api-keys-heading">
    <div className="border-b border-border pb-5">
      <h2 id="api-keys-heading" className="text-lg font-semibold text-foreground">
        MCP API keys
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Connect AI tools like Cursor or Claude to your RadEstate account. Each key acts as you —
        treat it like a password.
      </p>
    </div>

    <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-5">
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

      <AccountField
        id="api-key-expires"
        label="Expires in (days)"
        type="number"
        value={expiresInDays}
        onChange={onChangeExpiresInDays}
        error={errors.expiresInDays}
        autoComplete="off"
      />
      <p className="-mt-3 text-xs text-muted-foreground">
        Leave blank for a key that never expires.
      </p>

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

      {loadError ? (
        <p className="mt-3 text-sm text-destructive" role="alert">
          {loadError}
        </p>
      ) : null}

      {loading ? <p className="mt-3 text-sm text-muted-foreground">Loading keys…</p> : null}

      {!loading && !loadError && keys.length === 0 ? (
        <p className="mt-3 text-sm text-muted-foreground">
          You have no API keys yet. Create one above to connect an AI tool.
        </p>
      ) : null}

      {keys.length > 0 ? (
        <ul className="mt-2 divide-y divide-border">
          {keys.map((apiKey) => (
            <KeyRow
              key={apiKey.id}
              apiKey={apiKey}
              revoking={revokingId === apiKey.id}
              onRevoke={onRevoke}
            />
          ))}
        </ul>
      ) : null}
    </div>
  </section>
);
