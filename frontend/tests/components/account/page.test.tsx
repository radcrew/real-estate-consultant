// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AccountPage } from "@components/account/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
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
    await waitFor(() => expect(screen.getByRole("heading", { name: /personal information/i })).toBeInTheDocument());
  });

  it("renders account sidebar navigation", async () => {
    mockUseAuth.mockReturnValue({ session: { user: { email: "jane@test.com", avatarUrl: null } }, ready: true, refresh: vi.fn() });
    render(<AccountPage />);
    await waitFor(() => expect(screen.getByRole("navigation", { name: /account navigation/i })).toBeInTheDocument());
  });
});
