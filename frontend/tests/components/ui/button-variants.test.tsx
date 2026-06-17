// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ButtonPrimary } from "@components/ui/button-primary";
import { ButtonSecondary } from "@components/ui/button-secondary";
import { ButtonThird } from "@components/ui/button-third";
import { ButtonCircle } from "@components/ui/button-circle";

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe("ButtonPrimary", () => {
  it("renders a button with given text", () => {
    render(<ButtonPrimary>Save</ButtonPrimary>);
    expect(screen.getByRole("button", { name: "Save" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<ButtonPrimary onClick={onClick}>Save</ButtonPrimary>);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is disabled when disabled prop is set", () => {
    render(<ButtonPrimary disabled>Save</ButtonPrimary>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("applies custom className", () => {
    render(<ButtonPrimary className="w-full">Save</ButtonPrimary>);
    expect(screen.getByRole("button")).toHaveClass("w-full");
  });
});

describe("ButtonSecondary", () => {
  it("renders a button", () => {
    render(<ButtonSecondary>Cancel</ButtonSecondary>);
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("is disabled when disabled prop is set", () => {
    render(<ButtonSecondary disabled>Cancel</ButtonSecondary>);
    expect(screen.getByRole("button")).toBeDisabled();
  });
});

describe("ButtonThird", () => {
  it("renders a button", () => {
    render(<ButtonThird>Clear</ButtonThird>);
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<ButtonThird className="text-sm">Clear</ButtonThird>);
    expect(screen.getByRole("button")).toHaveClass("text-sm");
  });
});

describe("ButtonCircle", () => {
  it("renders a button", () => {
    render(<ButtonCircle aria-label="Next" />);
    expect(screen.getByRole("button", { name: "Next" })).toBeInTheDocument();
  });

  it("applies default size classes", () => {
    render(<ButtonCircle aria-label="btn" />);
    expect(screen.getByRole("button")).toHaveClass("w-9", "h-9");
  });

  it("applies custom size", () => {
    render(<ButtonCircle aria-label="btn" size="w-12 h-12" />);
    expect(screen.getByRole("button")).toHaveClass("w-12", "h-12");
  });

  it("is disabled when disabled prop is set", () => {
    render(<ButtonCircle aria-label="btn" disabled />);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("calls onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<ButtonCircle aria-label="btn" onClick={onClick} />);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
