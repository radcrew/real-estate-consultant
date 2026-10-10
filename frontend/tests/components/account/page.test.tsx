// @vitest-environment jsdom
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AxiosError, AxiosHeaders } from "axios";
import { AccountPage } from "@components/account/page";
import { accountService } from "@services/account";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/account",
}));
vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));
vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

const mockUseAuth = vi.fn();
vi.mock("@contexts/auth", () => ({ useAuth: () => mockUseAuth() }));

const mockGetProfile = vi.fn();
vi.mock("@services/account", () => ({
  accountService: { getProfile: (...a: unknown[]) => mockGetProfile(...a), updateProfile: vi.fn(), uploadAvatar: vi.fn(), changePassword: vi.fn() },
  mapProfileResponseToForm: () => ({ firstName: "Jane", lastName: "Doe", email: "jane@test.com", phone: "", address: "", city: "", state: "", zipCode: "", country: "" }),
  buildProfileUpdateBody: () => ({}),
}));
vi.mock("@lib/auth-session", () => ({
  readSession: () => null,
  saveSession: vi.fn(),
}));
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ savedIds: [], isSaved: () => false, ready: true, signedIn: true }),
}));
vi.mock("@services/listings", () => ({
  listingsService: {
    getListing: vi.fn(),
    getFeaturedListings: vi.fn().mockResolvedValue({ listings: [] }),
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockGetProfile.mockResolvedValue({ avatar_url: null });
});

describe("AccountPage", () => {
  it("returns null when not ready", () => {
    mockUseAuth.mockReturnValue({ session: null, ready: false, refresh: vi.fn() });
    const { container } = render(<AccountPage />);
    expect(container.firstChild).toBeNull();
  });

  it("returns null when ready but no session", () => {
    mockUseAuth.mockReturnValue({ session: null, ready: true, refresh: vi.fn() });
    const { container } = render(<AccountPage />);
    expect(container.firstChild).toBeNull();
  });

  it("renders account page when signed in", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    await waitFor(() => expect(screen.getByRole("region", { name: /personal information/i })).toBeInTheDocument());
  });

  it("renders account sidebar navigation", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    await waitFor(() => expect(screen.getByRole("navigation", { name: /account navigation/i })).toBeInTheDocument());
  });

  it("shows saved properties in-panel and keeps the sidebar", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    const nav = await screen.findByRole("navigation", { name: /account navigation/i });

    fireEvent.click(screen.getByRole("button", { name: /saved/i }));

    expect(await screen.findByRole("heading", { name: /saved properties/i })).toBeInTheDocument();
    expect(nav).toBeInTheDocument();
  });

  it("keeps the sidebar when browsing properties from the empty Saved tab", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    const nav = await screen.findByRole("navigation", { name: /account navigation/i });
    fireEvent.click(screen.getByRole("button", { name: /saved/i }));

    // The CTA must act in-panel, not navigate to /listings and drop the rail.
    const browse = await screen.findByRole("button", { name: /browse properties/i });
    fireEvent.click(browse);

    expect(await screen.findByRole("button", { name: /back to saved properties/i })).toBeInTheDocument();
    expect(nav).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: /saved properties/i })).not.toBeInTheDocument();
  });

  it("returns to the saved list from the browse panel", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    await screen.findByRole("navigation", { name: /account navigation/i });
    fireEvent.click(screen.getByRole("button", { name: /saved/i }));
    fireEvent.click(await screen.findByRole("button", { name: /browse properties/i }));

    fireEvent.click(await screen.findByRole("button", { name: /back to saved properties/i }));

    expect(await screen.findByRole("heading", { name: /saved properties/i })).toBeInTheDocument();
  });

  it("drops the browse panel when another tab is selected", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    await screen.findByRole("navigation", { name: /account navigation/i });
    fireEvent.click(screen.getByRole("button", { name: /saved/i }));
    fireEvent.click(await screen.findByRole("button", { name: /browse properties/i }));

    fireEvent.click(screen.getByRole("button", { name: /security/i }));
    fireEvent.click(screen.getByRole("button", { name: /saved/i }));

    expect(await screen.findByRole("heading", { name: /saved properties/i })).toBeInTheDocument();
  });

  describe("password change errors", () => {
    const apiError = (status: number, detail: string) =>
      new AxiosError("failed", "ERR_BAD_REQUEST", undefined, undefined, {
        status,
        statusText: "",
        headers: {},
        config: { headers: new AxiosHeaders() },
        data: { detail },
      });

    const submitPasswordChange = async () => {
      mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
      render(<AccountPage />);
      await screen.findByRole("navigation", { name: /account navigation/i });
      fireEvent.click(screen.getByRole("button", { name: /security/i }));
      fireEvent.change(screen.getByLabelText("Current password"), { target: { value: "oldpass11" } });
      fireEvent.change(screen.getByLabelText("New password"), { target: { value: "newpass11" } });
      fireEvent.change(screen.getByLabelText("Confirm new password"), { target: { value: "newpass11" } });
      fireEvent.click(screen.getByRole("button", { name: /update password/i }));
    };

    it("shows a wrong current password on that field", async () => {
      vi.mocked(accountService.changePassword).mockRejectedValue(apiError(400, "Current password is incorrect."));
      await submitPasswordChange();

      await waitFor(() =>
        expect(screen.getByLabelText("Current password")).toHaveAttribute("aria-invalid", "true"),
      );
      expect(screen.getByText("Current password is incorrect.")).toBeInTheDocument();
    });

    it("shows any other 400 as a form error", async () => {
      const detail = "This account signs in with Google and has no password to change.";
      vi.mocked(accountService.changePassword).mockRejectedValue(apiError(400, detail));
      await submitPasswordChange();

      expect(await screen.findByText(detail)).toBeInTheDocument();
      expect(screen.getByLabelText("Current password")).toHaveAttribute("aria-invalid", "false");
    });
  });
});
