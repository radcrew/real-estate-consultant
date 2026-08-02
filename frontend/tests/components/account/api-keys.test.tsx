// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AccountApiKeysSection } from "@components/account/sections/api-keys";
import { ApiKeyCreatedDialog } from "@components/account/sections/api-keys/created-dialog";
import type { McpApiKey, McpApiKeyCreated } from "@services/account";

const key = (over: Partial<McpApiKey> = {}): McpApiKey => ({
  id: "key-1",
  name: "cursor",
  key_prefix: "rad_abc",
  scopes: ["*"],
  created_at: "2026-01-15T00:00:00Z",
  last_used_at: null,
  revoked_at: null,
  expires_at: null,
  ...over,
});

const BASE = {
  keys: [] as McpApiKey[],
  loading: false,
  loadError: null,
  name: "",
  scope: "*",
  expiresInDays: "",
  errors: {},
  creating: false,
  revokingId: null,
  confirmingRevokeId: null,
  onChangeName: vi.fn(),
  onChangeScope: vi.fn(),
  onChangeExpiresInDays: vi.fn(),
  onSubmit: vi.fn((e) => e.preventDefault()),
  onRequestRevoke: vi.fn(),
  onConfirmRevoke: vi.fn(),
  onCancelRevoke: vi.fn(),
};

describe("AccountApiKeysSection", () => {
  it("renders the empty state when there are no keys", () => {
    render(<AccountApiKeysSection {...BASE} />);
    expect(screen.getByText(/no api keys yet/i)).toBeInTheDocument();
  });

  it("does not offer the mcp:admin scope", () => {
    render(<AccountApiKeysSection {...BASE} />);
    const options = screen.getAllByRole("option").map((o) => o.getAttribute("value"));
    expect(options).toEqual(["*", "mcp:read", "mcp:write"]);
  });

  it("lists keys with their prefix and never a full key", () => {
    render(<AccountApiKeysSection {...BASE} keys={[key()]} />);
    expect(screen.getByText("cursor")).toBeInTheDocument();
    expect(screen.getByText(/rad_abc/)).toBeInTheDocument();
  });

  it("shows Never for a key that has not been used", () => {
    render(<AccountApiKeysSection {...BASE} keys={[key()]} />);
    expect(screen.getByText("Never")).toBeInTheDocument();
  });

  it("calls onSubmit when the create form is submitted", () => {
    const onSubmit = vi.fn((e) => e.preventDefault());
    render(<AccountApiKeysSection {...BASE} onSubmit={onSubmit} />);
    fireEvent.submit(screen.getByRole("button", { name: /create key/i }).closest("form")!);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  describe("revoke", () => {
    it("asks for confirmation before revoking", () => {
      const onRequestRevoke = vi.fn();
      const onConfirmRevoke = vi.fn();
      render(
        <AccountApiKeysSection
          {...BASE}
          keys={[key()]}
          onRequestRevoke={onRequestRevoke}
          onConfirmRevoke={onConfirmRevoke}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /^revoke cursor$/i }));
      expect(onRequestRevoke).toHaveBeenCalledTimes(1);
      expect(onConfirmRevoke).not.toHaveBeenCalled();
    });

    it("revokes only after the confirm button is clicked", () => {
      const onConfirmRevoke = vi.fn();
      render(
        <AccountApiKeysSection
          {...BASE}
          keys={[key()]}
          confirmingRevokeId="key-1"
          onConfirmRevoke={onConfirmRevoke}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /confirm revoking cursor/i }));
      expect(onConfirmRevoke).toHaveBeenCalledTimes(1);
    });

    it("offers a cancel out of the confirmation", () => {
      const onCancelRevoke = vi.fn();
      render(
        <AccountApiKeysSection
          {...BASE}
          keys={[key()]}
          confirmingRevokeId="key-1"
          onCancelRevoke={onCancelRevoke}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(onCancelRevoke).toHaveBeenCalledTimes(1);
    });
  });

  describe("inactive keys", () => {
    it("keeps revoked keys visible but marked, with no revoke button", () => {
      render(
        <AccountApiKeysSection {...BASE} keys={[key({ revoked_at: "2026-02-01T00:00:00Z" })]} />,
      );
      expect(screen.getByText("cursor")).toBeInTheDocument();
      expect(screen.getByText(/revoked/i)).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: /revoke cursor/i })).not.toBeInTheDocument();
    });

    it("marks a key whose expiry has passed without an explicit revoke", () => {
      render(<AccountApiKeysSection {...BASE} keys={[key({ expires_at: "2020-01-01T00:00:00Z" })]} />);
      expect(screen.getByText(/expired/i)).toBeInTheDocument();
    });
  });
});

const created: McpApiKeyCreated = {
  id: "key-1",
  name: "cursor",
  key_prefix: "rad_abc",
  api_key: "rad_abcdefghijklmnopqrstuvwxyz",
  scopes: ["*"],
  created_at: "2026-01-15T00:00:00Z",
  expires_at: null,
};

describe("ApiKeyCreatedDialog", () => {
  it("renders nothing until a key has been created", () => {
    render(<ApiKeyCreatedDialog apiKey={null} onDismiss={vi.fn()} />);
    expect(screen.queryByTestId("api-key-plaintext")).not.toBeInTheDocument();
  });

  it("shows the plaintext key once created", () => {
    render(<ApiKeyCreatedDialog apiKey={created} onDismiss={vi.fn()} />);
    expect(screen.getByTestId("api-key-plaintext")).toHaveTextContent(created.api_key);
  });

  it("warns that the key will not be shown again", () => {
    render(<ApiKeyCreatedDialog apiKey={created} onDismiss={vi.fn()} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/only time this key will be shown/i);
  });

  it("keeps Done disabled until the key is acknowledged", () => {
    render(<ApiKeyCreatedDialog apiKey={created} onDismiss={vi.fn()} />);
    const done = screen.getByRole("button", { name: /done/i });
    expect(done).toBeDisabled();
    fireEvent.click(screen.getByRole("checkbox"));
    expect(done).toBeEnabled();
  });

  it("does not dismiss until acknowledged", () => {
    const onDismiss = vi.fn();
    render(<ApiKeyCreatedDialog apiKey={created} onDismiss={onDismiss} />);
    fireEvent.click(screen.getByRole("button", { name: /done/i }));
    expect(onDismiss).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: /done/i }));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  it("removes the plaintext key from the DOM once dismissed", () => {
    const { rerender } = render(<ApiKeyCreatedDialog apiKey={created} onDismiss={vi.fn()} />);
    expect(screen.getByTestId("api-key-plaintext")).toBeInTheDocument();

    // The parent clears createdKey on dismiss — the key must not linger anywhere.
    rerender(<ApiKeyCreatedDialog apiKey={null} onDismiss={vi.fn()} />);
    expect(screen.queryByTestId("api-key-plaintext")).not.toBeInTheDocument();
    expect(document.body.textContent).not.toContain(created.api_key);
  });

  it("copies the key to the clipboard", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });

    render(<ApiKeyCreatedDialog apiKey={created} onDismiss={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /copy api key/i }));

    expect(writeText).toHaveBeenCalledWith(created.api_key);
    expect(await screen.findByRole("button", { name: /copied/i })).toBeInTheDocument();
  });
});
