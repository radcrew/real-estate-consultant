// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PasswordStrengthMeter } from "@components/account/sections/password/meter";

describe("PasswordStrengthMeter", () => {
  it("shows a dash when password is empty", () => {
    render(<PasswordStrengthMeter password="" />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("shows the strength label when password is non-empty", () => {
    render(<PasswordStrengthMeter password="abc" />);
    expect(screen.getByText("Very weak")).toBeInTheDocument();
  });

  it("shows 'Strong' for a fully scored password", () => {
    render(<PasswordStrengthMeter password="Abcdefghijkl1!" />);
    expect(screen.getByText("Strong")).toBeInTheDocument();
  });

  it("renders a meter with aria-valuenow reflecting the score", () => {
    render(<PasswordStrengthMeter password="Abcdefghijkl1!" />);
    const meter = screen.getByRole("meter");
    expect(meter).toHaveAttribute("aria-valuenow", "4");
  });

  it("renders aria-valuenow of 0 for empty password", () => {
    render(<PasswordStrengthMeter password="" />);
    expect(screen.getByRole("meter")).toHaveAttribute("aria-valuenow", "0");
  });

  it("has aria-live polite for screen readers", () => {
    render(<PasswordStrengthMeter password="" />);
    expect(screen.getByRole("meter").closest("[aria-live]")).toHaveAttribute("aria-live", "polite");
  });

  it("renders the hint text", () => {
    render(<PasswordStrengthMeter password="" />);
    expect(screen.getByText(/Use at least 8 characters/)).toBeInTheDocument();
  });

  it("applies an extra className when provided", () => {
    const { container } = render(
      <PasswordStrengthMeter password="" className="mt-4" />,
    );
    expect(container.firstChild).toHaveClass("mt-4");
  });
});
