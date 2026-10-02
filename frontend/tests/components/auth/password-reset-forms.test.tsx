// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ForgotPasswordForm } from "@components/auth/forms/forgot-password";
import { ResetPasswordForm } from "@components/auth/forms/reset-password";
import type { AuthContextValue } from "@contexts/auth";

const mockAuth: AuthContextValue = {
  signIn: vi.fn(),
  signInWithGoogle: vi.fn(),
  signUp: vi.fn(),
  confirmSignUp: vi.fn(),
  resendCode: vi.fn(),
  requestPasswordReset: vi.fn(),
  resetPassword: vi.fn(),
  clearError: vi.fn(),
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

const mockPush = vi.fn();
let emailParam: string | null = null;

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, refresh: vi.fn() }),
  useSearchParams: () => ({ get: (key: string) => (key === "email" ? emailParam : null) }),
}));

beforeEach(() => {
  mockPush.mockReset();
  emailParam = null;
  mockAuth.error = null;
  mockAuth.isSubmitting = false;
  mockAuth.requestPasswordReset = vi.fn(async (_email, onSuccess) => onSuccess());
  mockAuth.resetPassword = vi.fn(async (_values, onSuccess) => onSuccess());
});

describe("ForgotPasswordForm", () => {
  it("requests a code and moves to the reset page with the email", async () => {
    render(<ForgotPasswordForm />);
    await userEvent.type(screen.getByLabelText(/email/i), "jane@example.com");
    await userEvent.click(screen.getByRole("button", { name: /send reset code/i }));

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith("/reset-password?email=jane%40example.com"),
    );
    expect(mockAuth.requestPasswordReset).toHaveBeenCalledWith(
      "jane@example.com",
      expect.any(Function),
    );
  });

  it("shows a request error from context", () => {
    mockAuth.error = "Too many attempts. Please wait and try again.";
    render(<ForgotPasswordForm />);
    expect(screen.getByRole("alert")).toHaveTextContent(/too many attempts/i);
  });
});

describe("ResetPasswordForm", () => {
  const fill = async ({ code = "123456", password = "NewPass123!", confirm = "NewPass123!" } = {}) => {
    await userEvent.type(screen.getByLabelText(/reset code/i), code);
    await userEvent.type(screen.getByLabelText(/^new password/i), password);
    await userEvent.type(screen.getByLabelText(/confirm new password/i), confirm);
    await userEvent.click(screen.getByRole("button", { name: /update password/i }));
  };

  it("prefills the email from ?email and says a code was sent", () => {
    emailParam = "jane@example.com";
    render(<ResetPasswordForm />);
    expect(screen.getByLabelText(/email/i)).toHaveValue("jane@example.com");
    expect(screen.getByRole("status")).toHaveTextContent("jane@example.com");
  });

  it("submits email, code and new password, then shows the done state", async () => {
    emailParam = "jane@example.com";
    render(<ResetPasswordForm />);
    await fill();

    expect(mockAuth.resetPassword).toHaveBeenCalledWith(
      { email: "jane@example.com", code: "123456", password: "NewPass123!" },
      expect.any(Function),
    );
    expect(await screen.findByText(/your password has been updated/i)).toBeInTheDocument();
  });

  it("does not submit when the passwords differ", async () => {
    emailParam = "jane@example.com";
    render(<ResetPasswordForm />);
    await fill({ confirm: "Different1!" });

    expect(screen.getByRole("alert")).toHaveTextContent("Passwords do not match.");
    expect(mockAuth.resetPassword).not.toHaveBeenCalled();
  });

  it("sends a new code for the entered email", async () => {
    emailParam = "jane@example.com";
    render(<ResetPasswordForm />);
    await userEvent.click(screen.getByRole("button", { name: /send a new code/i }));

    expect(mockAuth.requestPasswordReset).toHaveBeenCalledWith(
      "jane@example.com",
      expect.any(Function),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(/new code/i);
  });

  it("disables 'send a new code' until there is an email", () => {
    render(<ResetPasswordForm />);
    expect(screen.getByRole("button", { name: /send a new code/i })).toBeDisabled();
  });

  it("shows a request error from context", () => {
    mockAuth.error = "Invalid verification code.";
    render(<ResetPasswordForm />);
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid verification code.");
  });
});
