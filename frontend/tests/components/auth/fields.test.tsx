// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EmailField } from "@components/auth/fields/email";
import { PasswordField } from "@components/auth/fields/password";
import { TextField } from "@components/auth/fields/text";

describe("EmailField", () => {
  it("renders a labeled email input", () => {
    render(<EmailField id="e" value="" onChange={vi.fn()} />);
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toHaveAttribute("type", "email");
  });

  it("uses a custom label", () => {
    render(<EmailField id="e" value="" onChange={vi.fn()} label="Work email" />);
    expect(screen.getByLabelText("Work email")).toBeInTheDocument();
  });

  it("is disabled when disabled prop is set", () => {
    render(<EmailField id="e" value="" onChange={vi.fn()} disabled />);
    expect(screen.getByLabelText("Email")).toBeDisabled();
  });

  it("displays the current value", () => {
    render(<EmailField id="e" value="jane@example.com" onChange={vi.fn()} />);
    expect(screen.getByLabelText("Email")).toHaveValue("jane@example.com");
  });
});

describe("PasswordField", () => {
  it("renders a labeled password input", () => {
    render(<PasswordField id="p" value="" onChange={vi.fn()} autoComplete="current-password" />);
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toHaveAttribute("type", "password");
  });

  it("uses a custom label", () => {
    render(
      <PasswordField id="p" value="" onChange={vi.fn()} autoComplete="new-password" label="Confirm password" />,
    );
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
  });

  it("applies default minLength and maxLength", () => {
    render(<PasswordField id="p" value="" onChange={vi.fn()} autoComplete="new-password" />);
    expect(screen.getByLabelText("Password")).toHaveAttribute("minlength", "8");
    expect(screen.getByLabelText("Password")).toHaveAttribute("maxlength", "72");
  });

  it("accepts custom minLength and maxLength", () => {
    render(
      <PasswordField id="p" value="" onChange={vi.fn()} autoComplete="new-password" minLength={6} maxLength={50} />,
    );
    expect(screen.getByLabelText("Password")).toHaveAttribute("minlength", "6");
    expect(screen.getByLabelText("Password")).toHaveAttribute("maxlength", "50");
  });

  it("renders children below the input", () => {
    render(
      <PasswordField id="p" value="" onChange={vi.fn()} autoComplete="new-password">
        <p>Use at least 8 characters.</p>
      </PasswordField>,
    );
    expect(screen.getByText("Use at least 8 characters.")).toBeInTheDocument();
  });

  it("is disabled when disabled prop is set", () => {
    render(<PasswordField id="p" value="" onChange={vi.fn()} autoComplete="new-password" disabled />);
    expect(screen.getByLabelText("Password")).toBeDisabled();
  });
});

describe("TextField", () => {
  it("renders a labeled text input", () => {
    render(<TextField id="fn" label="First name" value="" onChange={vi.fn()} />);
    expect(screen.getByLabelText("First name")).toBeInTheDocument();
    expect(screen.getByLabelText("First name")).toHaveAttribute("type", "text");
  });

  it("displays the current value", () => {
    render(<TextField id="fn" label="First name" value="Jane" onChange={vi.fn()} />);
    expect(screen.getByLabelText("First name")).toHaveValue("Jane");
  });

  it("is disabled when disabled prop is set", () => {
    render(<TextField id="fn" label="First name" value="" onChange={vi.fn()} disabled />);
    expect(screen.getByLabelText("First name")).toBeDisabled();
  });
});
