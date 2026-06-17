// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GoogleAuthButton } from "@components/auth/forms/button";
import type { AuthContextValue } from "@contexts/auth";

const mockAuth: AuthContextValue = {
  signIn: vi.fn(),
  signInWithGoogle: vi.fn(),
  signUp: vi.fn(),
  signOut: vi.fn(),
  refresh: vi.fn(),
  session: null,
  ready: true,
  error: null,
  isSubmitting: false,
};

vi.mock("@contexts/auth", () => ({ useAuth: () => mockAuth }));
vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

beforeEach(() => {
  mockAuth.signInWithGoogle = vi.fn();
  mockAuth.isSubmitting = false;
});

describe("GoogleAuthButton", () => {
  it("renders the default label", () => {
    render(<GoogleAuthButton />);
    expect(screen.getByRole("button", { name: /continue with google/i })).toBeInTheDocument();
  });

  it("renders a custom label", () => {
    render(<GoogleAuthButton label="Sign up with Google" />);
    expect(screen.getByRole("button", { name: /sign up with google/i })).toBeInTheDocument();
  });

  it("calls signInWithGoogle when clicked", async () => {
    render(<GoogleAuthButton />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockAuth.signInWithGoogle).toHaveBeenCalledOnce();
  });

  it("is disabled while submitting", () => {
    mockAuth.isSubmitting = true;
    render(<GoogleAuthButton />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("does not call signInWithGoogle when disabled", async () => {
    mockAuth.isSubmitting = true;
    render(<GoogleAuthButton />);
    await userEvent.click(screen.getByRole("button"));
    expect(mockAuth.signInWithGoogle).not.toHaveBeenCalled();
  });
});
