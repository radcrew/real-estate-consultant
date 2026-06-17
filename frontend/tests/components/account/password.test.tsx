// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AccountPasswordSection } from "@components/account/sections/password";

const BASE = {
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
  errors: {},
  submitting: false,
  success: false,
  onChangeCurrent: vi.fn(),
  onChangeNew: vi.fn(),
  onChangeConfirm: vi.fn(),
  onSubmit: vi.fn((e) => e.preventDefault()),
};

describe("AccountPasswordSection", () => {
  it("renders the security heading", () => {
    render(<AccountPasswordSection {...BASE} />);
    expect(screen.getByRole("heading", { name: /security/i })).toBeInTheDocument();
  });

  it("renders update password submit button", () => {
    render(<AccountPasswordSection {...BASE} />);
    expect(screen.getByRole("button", { name: /update password/i })).toBeInTheDocument();
  });

  it("shows updating label when submitting", () => {
    render(<AccountPasswordSection {...BASE} submitting={true} />);
    expect(screen.getByRole("button", { name: /updating/i })).toBeDisabled();
  });

  it("shows success message when success is true", () => {
    render(<AccountPasswordSection {...BASE} success={true} />);
    expect(screen.getByRole("status")).toHaveTextContent(/password updated/i);
  });

  it("shows form-level error when provided", () => {
    render(<AccountPasswordSection {...BASE} errors={{ form: "Current password is wrong." }} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Current password is wrong.");
  });

  it("calls onSubmit when form is submitted", () => {
    const onSubmit = vi.fn((e) => e.preventDefault());
    render(<AccountPasswordSection {...BASE} onSubmit={onSubmit} />);
    fireEvent.submit(screen.getByRole("button", { name: /update password/i }).closest("form")!);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
