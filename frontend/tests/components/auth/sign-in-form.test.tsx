// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SignInForm } from "@components/auth/forms/sign-in";
import type { AuthContextValue } from "@contexts/auth";

// ---------------------------------------------------------------------------
// Controllable mock — each test can override fields via mockAuth
// ---------------------------------------------------------------------------

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

vi.mock("@contexts/auth", () => ({
  useAuth: () => mockAuth,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }),
  useSearchParams: () => ({ get: vi.fn().mockReturnValue(null) }),
}));

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} />,
}));

beforeEach(() => {
  mockAuth.signIn = vi.fn();
  mockAuth.error = null;
  mockAuth.isSubmitting = false;
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("SignInForm", () => {
  it("renders email and password fields", () => {
    render(<SignInForm />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it("renders the sign in button", () => {
    render(<SignInForm />);
    expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
  });

  it("calls signIn with typed email and password on submit", async () => {
    render(<SignInForm />);
    await userEvent.type(screen.getByLabelText(/email/i), "jane@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "secret123");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => {
      expect(mockAuth.signIn).toHaveBeenCalledWith(
        { email: "jane@example.com", password: "secret123" },
        expect.any(Function),
      );
    });
  });

  it("shows an error alert when context has an error", () => {
    mockAuth.error = "Invalid credentials.";
    render(<SignInForm />);
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials.");
  });

  it("does not show an error alert when error is null", () => {
    render(<SignInForm />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows 'Signing in…' label and disables button while submitting", () => {
    mockAuth.isSubmitting = true;
    render(<SignInForm />);
    expect(screen.getByRole("button", { name: /signing in/i })).toBeDisabled();
  });

  it("disables email and password fields while submitting", () => {
    mockAuth.isSubmitting = true;
    render(<SignInForm />);
    expect(screen.getByLabelText(/email/i)).toBeDisabled();
    expect(screen.getByLabelText(/password/i)).toBeDisabled();
  });
});
