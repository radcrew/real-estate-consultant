// @vitest-environment jsdom
import { act, render, screen, waitFor } from "@testing-library/react";
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
  confirmSignUp: vi.fn(),
  resendCode: vi.fn(),
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

const mockPush = vi.fn();
const mockNext = vi.fn().mockReturnValue(null);

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, refresh: vi.fn() }),
  useSearchParams: () => ({ get: mockNext }),
}));

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} />,
}));

beforeEach(() => {
  mockAuth.signIn = vi.fn();
  mockAuth.confirmSignUp = vi.fn();
  mockNext.mockReturnValue(null);
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
        expect.any(Function),
      );
    });
  });

  it("verifies an unconfirmed account in place and then signs in with the typed password", async () => {
    render(<SignInForm />);
    await userEvent.type(screen.getByLabelText(/email/i), "jane@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "secret123");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));
    await waitFor(() => expect(mockAuth.signIn).toHaveBeenCalled());

    const onUnconfirmed = vi.mocked(mockAuth.signIn).mock.calls[0][2]!;
    act(() => onUnconfirmed());
    expect(mockPush).not.toHaveBeenCalled();
    expect(screen.getByText("We sent a verification code to jane@example.com.")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/verification code/i), "123456");
    await userEvent.click(screen.getByRole("button", { name: /verify email/i }));
    await waitFor(() => expect(mockAuth.confirmSignUp).toHaveBeenCalled());

    const [email, code, onVerified] = vi.mocked(mockAuth.confirmSignUp).mock.calls[0];
    expect([email, code]).toEqual(["jane@example.com", "123456"]);
    vi.mocked(mockAuth.signIn).mockClear();
    await act(() => onVerified());
    expect(mockAuth.signIn).toHaveBeenCalledWith(
      { email: "jane@example.com", password: "secret123" },
      expect.any(Function),
    );
  });

  it("keeps the next path when verifying in place", async () => {
    mockNext.mockReturnValue("/saved");
    const assign = vi.fn();
    vi.spyOn(window, "location", "get").mockReturnValue({ assign } as unknown as Location);
    // First call (the sign-in form) finds the account unconfirmed; the second, after
    // the code, succeeds.
    mockAuth.signIn = vi.fn(async (_creds, onSuccess, onUnconfirmed) =>
      onUnconfirmed ? onUnconfirmed() : onSuccess(),
    );
    mockAuth.confirmSignUp = vi.fn(async (_email, _code, onSuccess) => onSuccess());
    render(<SignInForm />);
    await userEvent.type(screen.getByLabelText(/email/i), "jane@example.com");
    await userEvent.type(screen.getByLabelText(/password/i), "secret123");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await userEvent.type(await screen.findByLabelText(/verification code/i), "123456");
    await userEvent.click(screen.getByRole("button", { name: /verify email/i }));

    await waitFor(() =>
      expect(assign).toHaveBeenCalledWith("/auth/cognito-logout?next=%2Fsaved"),
    );
    vi.restoreAllMocks();
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
