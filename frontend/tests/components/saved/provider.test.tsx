// @vitest-environment jsdom
import { render, screen, act, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { SavedListingsProvider, useSavedListings } from "@components/saved/provider";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockGetSavedIds = vi.fn();
const mockAddSaved = vi.fn();
const mockRemoveSaved = vi.fn();
vi.mock("@services/account", () => ({
  accountService: {
    getSavedIds: (...args: unknown[]) => mockGetSavedIds(...args),
    addSaved: (...args: unknown[]) => mockAddSaved(...args),
    removeSaved: (...args: unknown[]) => mockRemoveSaved(...args),
  },
}));

const mockUseAuth = vi.fn();
vi.mock("@contexts/auth", () => ({
  useAuth: () => mockUseAuth(),
}));

const Consumer = () => {
  const { savedIds, isSaved, toggle, ready, signedIn } = useSavedListings();
  return (
    <div>
      <span data-testid="ready">{String(ready)}</span>
      <span data-testid="signed-in">{String(signedIn)}</span>
      <span data-testid="count">{savedIds.length}</span>
      <span data-testid="is-saved-a">{String(isSaved("a"))}</span>
      <button onClick={() => toggle("a")}>toggle-a</button>
    </div>
  );
};

const renderWithProvider = () =>
  render(
    <SavedListingsProvider>
      <Consumer />
    </SavedListingsProvider>,
  );

beforeEach(() => {
  vi.clearAllMocks();
  mockAddSaved.mockResolvedValue(undefined);
  mockRemoveSaved.mockResolvedValue(undefined);
});

describe("SavedListingsProvider — signed out", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ session: null, ready: true });
  });

  it("is ready and not signed-in", async () => {
    renderWithProvider();
    await waitFor(() => expect(screen.getByTestId("ready").textContent).toBe("true"));
    expect(screen.getByTestId("signed-in").textContent).toBe("false");
    expect(screen.getByTestId("count").textContent).toBe("0");
  });

  it("redirects to sign-in when toggle called while signed out", async () => {
    renderWithProvider();
    await waitFor(() => expect(screen.getByTestId("ready").textContent).toBe("true"));
    await act(async () => screen.getByRole("button").click());
    expect(mockPush).toHaveBeenCalledWith("/sign-in");
  });
});

describe("SavedListingsProvider — signed in", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ session: { user: { id: "u1" } }, ready: true });
    mockGetSavedIds.mockResolvedValue(["a", "b"]);
  });

  it("loads saved ids and marks ready", async () => {
    renderWithProvider();
    await waitFor(() => expect(screen.getByTestId("ready").textContent).toBe("true"));
    expect(screen.getByTestId("count").textContent).toBe("2");
    expect(screen.getByTestId("is-saved-a").textContent).toBe("true");
  });

  it("toggle adds a new id optimistically", async () => {
    mockGetSavedIds.mockResolvedValue([]);
    renderWithProvider();
    await waitFor(() => expect(screen.getByTestId("ready").textContent).toBe("true"));
    await act(async () => screen.getByRole("button").click());
    expect(screen.getByTestId("is-saved-a").textContent).toBe("true");
    expect(mockAddSaved).toHaveBeenCalledWith("a", expect.anything());
  });

  it("toggle removes an existing id optimistically", async () => {
    renderWithProvider();
    await waitFor(() => expect(screen.getByTestId("is-saved-a").textContent).toBe("true"));
    await act(async () => screen.getByRole("button").click());
    expect(screen.getByTestId("is-saved-a").textContent).toBe("false");
    expect(mockRemoveSaved).toHaveBeenCalledWith("a", expect.anything());
  });
});
