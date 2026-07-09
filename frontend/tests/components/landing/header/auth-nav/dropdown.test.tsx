// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfileDropdown } from "@components/landing/header/auth-nav/dropdown";
import type { AuthContextValue } from "@contexts/auth";

const mockAuth: AuthContextValue = {
  session: { user: { id: "u1", email: "jane@example.com" } } as AuthContextValue["session"],
  ready: true,
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
  default: ({ href, children, onClick }: { href: string; children: React.ReactNode; onClick?: () => void }) => (
    <a href={href} onClick={onClick}>{children}</a>
  ),
}));

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

describe("ProfileDropdown", () => {
  it("closes when clicking outside the menu", async () => {
    render(
      <div>
        <ProfileDropdown />
        <div data-testid="outside">Outside content</div>
      </div>,
    );

    fireEvent.click(screen.getByLabelText("Account menu"));
    expect(screen.getByText("Account")).toBeInTheDocument();

    fireEvent.mouseDown(screen.getByTestId("outside"));
    await waitFor(() => expect(screen.queryByText("Account")).not.toBeInTheDocument());
  });

  it("closes when the profile button is clicked again", async () => {
    render(<ProfileDropdown />);

    const button = screen.getByLabelText("Account menu");
    fireEvent.click(button);
    expect(screen.getByText("Account")).toBeInTheDocument();

    fireEvent.click(button);
    await waitFor(() => expect(screen.queryByText("Account")).not.toBeInTheDocument());
  });
});
