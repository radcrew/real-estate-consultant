// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { AccountField } from "@components/account/field";

describe("AccountField", () => {
  it("renders a labeled input", () => {
    render(<AccountField id="name" label="Full name" value="" onChange={vi.fn()} />);
    expect(screen.getByLabelText("Full name")).toBeInTheDocument();
  });

  it("displays the current value", () => {
    render(<AccountField id="name" label="Full name" value="Jane Doe" onChange={vi.fn()} />);
    expect(screen.getByLabelText("Full name")).toHaveValue("Jane Doe");
  });

  it("calls onChange with the new value when user types", async () => {
    const onChange = vi.fn();
    render(<AccountField id="name" label="Full name" value="" onChange={onChange} />);
    await userEvent.type(screen.getByLabelText("Full name"), "J");
    expect(onChange).toHaveBeenCalledWith("J");
  });

  it("shows an error message when error prop is provided", () => {
    render(
      <AccountField id="email" label="Email" value="" onChange={vi.fn()} error="Invalid email" />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid email");
  });

  it("sets aria-invalid when error is provided", () => {
    render(
      <AccountField id="email" label="Email" value="" onChange={vi.fn()} error="Bad" />,
    );
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-invalid", "true");
  });

  it("sets aria-describedby to the error element id when error is provided", () => {
    render(
      <AccountField id="email" label="Email" value="" onChange={vi.fn()} error="Bad" />,
    );
    expect(screen.getByLabelText("Email")).toHaveAttribute("aria-describedby", "email-error");
    expect(screen.getByRole("alert")).toHaveAttribute("id", "email-error");
  });

  it("does not show an error message when error is null", () => {
    render(<AccountField id="name" label="Full name" value="" onChange={vi.fn()} error={null} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("is disabled when disabled prop is set", () => {
    render(<AccountField id="name" label="Full name" value="" onChange={vi.fn()} disabled />);
    expect(screen.getByLabelText("Full name")).toBeDisabled();
  });

  it("is readOnly when readOnly prop is set", () => {
    render(<AccountField id="name" label="Full name" value="Jane" onChange={vi.fn()} readOnly />);
    expect(screen.getByLabelText("Full name")).toHaveAttribute("readonly");
  });

  it("applies custom className to the wrapper", () => {
    const { container } = render(
      <AccountField id="name" label="Full name" value="" onChange={vi.fn()} className="col-span-2" />,
    );
    expect(container.firstChild).toHaveClass("col-span-2");
  });
});
