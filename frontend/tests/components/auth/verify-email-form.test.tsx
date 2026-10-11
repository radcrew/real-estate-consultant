// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { VerifyEmailForm } from "@components/auth/forms/verify-email";
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

const mockAssign = vi.fn();

beforeEach(() => {
  mockAssign.mockReset();
  vi.spyOn(window, "location", "get").mockReturnValue({
    assign: mockAssign,
  } as unknown as Location);
  mockAuth.error = null;
  mockAuth.isSubmitting = false;
  // Each action succeeds immediately by running its success callback.
  mockAuth.confirmSignUp = vi.fn(async (_email, _code, onSuccess) => onSuccess());
  mockAuth.resendCode = vi.fn(async (_email, onSuccess) => onSuccess());
  mockAuth.signIn = vi.fn(async (_creds, onSuccess) => onSuccess());
});

afterEach(() => {
  vi.restoreAllMocks();
});

const submitCode = async (code = "123456") => {
  await userEvent.type(screen.getByLabelText(/verification code/i), code);
  await userEvent.click(screen.getByRole("button", { name: /verify email/i }));
};

describe("VerifyEmailForm", () => {
  it("tells the user where the code was sent", () => {
    render(<VerifyEmailForm email="jane@example.com" />);
    expect(screen.getByRole("status")).toHaveTextContent("jane@example.com");
  });

  it("confirms the code, signs in, then clears Cognito's session on the way home", async () => {
    render(<VerifyEmailForm email="jane@example.com" password="Secret123!" />);
    await submitCode();
    await waitFor(() => expect(mockAssign).toHaveBeenCalledWith("/auth/cognito-logout"));
    expect(mockAuth.confirmSignUp).toHaveBeenCalledWith(
      "jane@example.com",
      "123456",
      expect.any(Function),
    );
    expect(mockAuth.signIn).toHaveBeenCalledWith(
      { email: "jane@example.com", password: "Secret123!" },
      expect.any(Function),
    );
  });

  it("passes the sign-in page's next path through the logout", async () => {
    render(<VerifyEmailForm email="jane@example.com" password="Secret123!" next="/saved" />);
    await submitCode();
    await waitFor(() =>
      expect(mockAssign).toHaveBeenCalledWith("/auth/cognito-logout?next=%2Fsaved"),
    );
  });

  it("clears Cognito's session even when the password is not known", async () => {
    render(<VerifyEmailForm email="jane@example.com" />);
    await submitCode();
    await waitFor(() => expect(mockAssign).toHaveBeenCalledWith("/auth/cognito-logout"));
    expect(mockAuth.signIn).not.toHaveBeenCalled();
  });

  it("resends the code and says so", async () => {
    render(<VerifyEmailForm email="jane@example.com" />);
    await userEvent.click(screen.getByRole("button", { name: /resend code/i }));
    expect(mockAuth.resendCode).toHaveBeenCalledWith("jane@example.com", expect.any(Function));
    expect(await screen.findByRole("status")).toHaveTextContent(/new code/i);
  });

  it("shows a request error from context", () => {
    mockAuth.error = "Invalid verification code.";
    render(<VerifyEmailForm email="jane@example.com" />);
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid verification code.");
  });
});
