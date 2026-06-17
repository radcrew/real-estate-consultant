// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthNav } from "@components/landing/header/auth-nav";
import type { AuthContextValue } from "@contexts/auth";

const mockAuth: AuthContextValue = {
  session: null,
  ready: false,
  signIn: vi.fn(),
  signInWithGoogle: vi.fn(),
  signUp: vi.fn(),
  signOut: vi.fn(),
  refresh: vi.fn(),
  error: null,
  isSubmitting: false,
};

vi.mock("@contexts/auth", () => ({ useAuth: () => mockAuth }));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@components/landing/header/auth-nav/dropdown", () => ({
  ProfileDropdown: () => <div data-testid="profile-dropdown" />,
}));

beforeEach(() => {
  mockAuth.session = null;
  mockAuth.ready = false;
});

describe("AuthNav", () => {
  it("shows a loading skeleton when not ready", () => {
    mockAuth.ready = false;
    render(<AuthNav />);
    expect(screen.getByLabelText("Loading account")).toBeInTheDocument();
  });

  it("shows sign-in and get-started links when signed out", () => {
    mockAuth.ready = true;
    mockAuth.session = null;
    render(<AuthNav />);
    expect(screen.getByRole("link", { name: "Sign In" })).toHaveAttribute("href", "/sign-in");
    expect(screen.getByRole("link", { name: "Get Started" })).toHaveAttribute("href", "/sign-up");
  });

  it("shows profile dropdown when signed in", () => {
    mockAuth.ready = true;
    mockAuth.session = { user: { id: "u1" } } as AuthContextValue["session"];
    render(<AuthNav />);
    expect(screen.getByTestId("profile-dropdown")).toBeInTheDocument();
  });
});
