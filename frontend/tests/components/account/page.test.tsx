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
const mockBuildBody = vi.fn();
vi.mock("@services/account", () => ({
  accountService: { getProfile: (...a: unknown[]) => mockGetProfile(...a), updateProfile: vi.fn(), uploadAvatar: vi.fn(), changePassword: vi.fn(), verifyEmail: vi.fn() },
  mapProfileResponseToForm: (r: { email?: string | null }) => ({ firstName: "Jane", lastName: "Doe", email: r?.email ?? "jane@test.com", phone: "", address: "", city: "", state: "", zipCode: "", country: "" }),
  buildProfileUpdateBody: (...a: unknown[]) => mockBuildBody(...a),
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
  mockBuildBody.mockReturnValue({});
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

  describe("email change", () => {
    const requestEmailChange = async () => {
      mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
      mockBuildBody.mockReturnValue({ email: "new@test.com" });
      vi.mocked(accountService.updateProfile).mockResolvedValue({
        email: "jane@test.com",
        email_change_pending: true,
      } as Awaited<ReturnType<typeof accountService.updateProfile>>);
      render(<AccountPage />);
      fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
      fireEvent.click(screen.getByRole("button", { name: "Save" }));
      return screen.findByRole("region", { name: /confirm new email/i });
    };

    it("asks for the code after a new email is saved", async () => {
      await requestEmailChange();
      expect(screen.getByText(/We sent a code to new@test.com/)).toBeInTheDocument();
    });

    it("finishes the change with the code and drops the code form", async () => {
      await requestEmailChange();
      vi.mocked(accountService.verifyEmail).mockResolvedValue({
        email: "new@test.com",
      } as Awaited<ReturnType<typeof accountService.verifyEmail>>);

      fireEvent.change(screen.getByLabelText("Verification code"), { target: { value: " 123456 " } });
      fireEvent.click(screen.getByRole("button", { name: /verify email/i }));

      expect(await screen.findByText("Email updated.")).toBeInTheDocument();
      expect(accountService.verifyEmail).toHaveBeenCalledWith("123456");
      expect(screen.queryByRole("region", { name: /confirm new email/i })).not.toBeInTheDocument();
    });

    it("shows a rejected code on the code field", async () => {
      await requestEmailChange();
      vi.mocked(accountService.verifyEmail).mockRejectedValue(
        new AxiosError("failed", "ERR_BAD_REQUEST", undefined, undefined, {
          status: 400,
          statusText: "",
          headers: {},
          config: { headers: new AxiosHeaders() },
          data: { detail: "Invalid verification code." },
        }),
      );

      fireEvent.change(screen.getByLabelText("Verification code"), { target: { value: "000000" } });
      fireEvent.click(screen.getByRole("button", { name: /verify email/i }));

      expect(await screen.findByText("Invalid verification code.")).toBeInTheDocument();
      expect(screen.getByRole("region", { name: /confirm new email/i })).toBeInTheDocument();
    });

    it("resends by asking for the same email again", async () => {
      await requestEmailChange();
      vi.mocked(accountService.updateProfile).mockClear();

      fireEvent.click(screen.getByRole("button", { name: /resend code/i }));

      expect(await screen.findByText("We sent a new code to new@test.com.")).toBeInTheDocument();
      expect(accountService.updateProfile).toHaveBeenCalledWith({ email: "new@test.com" });
    });
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
