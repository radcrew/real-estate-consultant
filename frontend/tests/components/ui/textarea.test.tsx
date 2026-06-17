// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Textarea } from "@components/ui/textarea";

describe("Textarea", () => {
  it("renders a textarea element", () => {
    render(<Textarea />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("defaults to 4 rows", () => {
    render(<Textarea />);
    expect(screen.getByRole("textbox")).toHaveAttribute("rows", "4");
  });

  it("respects a custom rows value", () => {
    render(<Textarea rows={8} />);
    expect(screen.getByRole("textbox")).toHaveAttribute("rows", "8");
  });

  it("passes placeholder through", () => {
    render(<Textarea placeholder="Enter message" />);
    expect(screen.getByPlaceholderText("Enter message")).toBeInTheDocument();
  });

  it("calls onChange when user types", async () => {
    const onChange = vi.fn();
    render(<Textarea onChange={onChange} />);
    await userEvent.type(screen.getByRole("textbox"), "hello");
    expect(onChange).toHaveBeenCalled();
  });

  it("applies custom className", () => {
    render(<Textarea className="h-40" />);
    expect(screen.getByRole("textbox")).toHaveClass("h-40");
  });

  it("is disabled when disabled prop is set", () => {
    render(<Textarea disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("forwards ref to the underlying textarea", () => {
    let ref: HTMLTextAreaElement | null = null;
    render(<Textarea ref={(el) => { ref = el; }} />);
    expect(ref).toBeInstanceOf(HTMLTextAreaElement);
  });
});
