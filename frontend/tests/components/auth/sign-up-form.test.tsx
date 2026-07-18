// @vitest-environment jsdom
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SignUpForm } from "@components/auth/forms/sign-up";
import type { AuthContextValue } from "@contexts/auth";

// ---------------------------------------------------------------------------
// Controllable mock
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
}));

vi.mock("next/image", () => ({
  default: ({ alt }: { alt: string }) => <img alt={alt} />,
}));

beforeEach(() => {
  mockAuth.signUp = vi.fn();
  mockAuth.error = null;
  mockAuth.isSubmitting = false;
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const typeIfNonEmpty = async (el: HTMLElement, value: string) => {
  if (value) await userEvent.type(el, value);
};

const fillForm = async (overrides: Partial<{
  firstName: string; lastName: string; email: string;
  password: string; confirm: string;
}> = {}) => {
  const v = {
    firstName: "Jane", lastName: "Doe", email: "jane@example.com",
    password: "Secret123!", confirm: "Secret123!", ...overrides,
  };
  await typeIfNonEmpty(screen.getByLabelText(/first name/i), v.firstName);
  await typeIfNonEmpty(screen.getByLabelText(/last name/i), v.lastName);
  await typeIfNonEmpty(screen.getByLabelText(/email/i), v.email);
  const [passwordField, confirmField] = screen.getAllByLabelText(/password/i);
  await typeIfNonEmpty(passwordField, v.password);
  await typeIfNonEmpty(confirmField, v.confirm);
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("SignUpForm", () => {
  it("renders all required fields", () => {
    render(<SignUpForm />);
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getAllByLabelText(/password/i)).toHaveLength(2);
  });

  it("renders the create account button", () => {
    render(<SignUpForm />);
    expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
  });

  it("shows a validation error when passwords do not match", async () => {
    render(<SignUpForm />);
    await fillForm({ confirm: "different!" });
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Passwords do not match.");
  });

  it("shows a validation error when first name is empty", async () => {
    render(<SignUpForm />);
    await fillForm({ firstName: "" });
    // bypass native required-field constraint validation to exercise JS validation
    fireEvent.submit(screen.getByRole("button", { name: /create account/i }).closest("form")!);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/first name and last name are required/i);
    });
  });

  it("shows a validation error when last name is whitespace only", async () => {
    render(<SignUpForm />);
    await fillForm({ lastName: "   " });
    fireEvent.submit(screen.getByRole("button", { name: /create account/i }).closest("form")!);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/first name and last name are required/i);
    });
  });

  it("calls signUp with trimmed name fields on valid submit", async () => {
    render(<SignUpForm />);
    await fillForm({ firstName: "  Jane  ", lastName: "  Doe  " });
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    await waitFor(() => {
      expect(mockAuth.signUp).toHaveBeenCalledWith(
        expect.objectContaining({ firstName: "Jane", lastName: "Doe" }),
        expect.any(Function),
      );
    });
  });

  it("calls signUp with correct email and password on valid submit", async () => {
    render(<SignUpForm />);
    await fillForm();
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    await waitFor(() => {
      expect(mockAuth.signUp).toHaveBeenCalledWith(
        expect.objectContaining({ email: "jane@example.com", password: "Secret123!" }),
        expect.any(Function),
      );
    });
  });

  it("does not call signUp when passwords mismatch", async () => {
    render(<SignUpForm />);
    await fillForm({ confirm: "wrong" });
    await userEvent.click(screen.getByRole("button", { name: /create account/i }));
    expect(mockAuth.signUp).not.toHaveBeenCalled();
  });

  it("shows a request error from context", () => {
    mockAuth.error = "Email already in use.";
    render(<SignUpForm />);
    expect(screen.getByRole("alert")).toHaveTextContent("Email already in use.");
  });

  it("shows 'Creating account…' and disables button while submitting", () => {
    mockAuth.isSubmitting = true;
    render(<SignUpForm />);
    expect(screen.getByRole("button", { name: /creating account/i })).toBeDisabled();
  });
});
