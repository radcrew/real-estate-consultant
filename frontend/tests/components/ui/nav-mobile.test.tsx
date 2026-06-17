// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { NavMobile } from "@components/ui/nav-mobile";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@headlessui/react", () => ({
  Disclosure: ({ children }: { children: React.ReactNode }) => <li>{children}</li>,
  DisclosureButton: ({ children }: { children: React.ReactNode }) => <button>{children}</button>,
  DisclosurePanel: ({ children }: { children: React.ReactNode }) => <ul>{children}</ul>,
}));

vi.mock("@components/ui/switch-dark-mode", () => ({
  SwitchDarkMode: () => <button aria-label="Toggle dark mode" />,
}));

vi.mock("@components/ui/socials-list", () => ({
  SocialsList: () => <div data-testid="socials" />,
}));

vi.mock("@components/ui/logo", () => ({
  Logo: () => <div data-testid="logo" />,
}));

vi.mock("@components/ui/button-close", () => ({
  ButtonClose: ({ onClick }: { onClick?: () => void }) => <button onClick={onClick} aria-label="Close" />,
}));

const mockSignOut = vi.fn();
const mockUseAuth = vi.fn();
vi.mock("@contexts/auth", () => ({
  useAuth: () => mockUseAuth(),
}));

const NAV = [
  { id: "listings", name: "Listings", href: "/listings" },
];

describe("NavMobile — signed out", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ session: null, signOut: mockSignOut });
  });

  it("renders sign-in and sign-up links", () => {
    render(<NavMobile data={NAV} />);
    expect(screen.getByRole("link", { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /sign up/i })).toBeInTheDocument();
  });

  it("calls onClickClose when close button clicked", () => {
    const onClose = vi.fn();
    render(<NavMobile data={NAV} onClickClose={onClose} />);
    screen.getByRole("button", { name: /close/i }).click();
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("renders provided nav items", () => {
    render(<NavMobile data={NAV} />);
    expect(screen.getByRole("link", { name: "Listings" })).toHaveAttribute("href", "/listings");
  });
});

describe("NavMobile — signed in", () => {
  beforeEach(() => {
    mockUseAuth.mockReturnValue({ session: { user: { id: "u1" } }, signOut: mockSignOut });
  });

  it("renders your-account and sign-out links", () => {
    render(<NavMobile data={NAV} />);
    expect(screen.getByRole("link", { name: /your account/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });
});
