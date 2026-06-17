// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Input } from "@components/ui/input";

describe("Input", () => {
  it("renders an input element", () => {
    render(<Input />);
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("defaults to type=text", () => {
    render(<Input />);
    expect(screen.getByRole("textbox")).toHaveAttribute("type", "text");
  });

  it("respects an explicit type", () => {
    render(<Input type="email" />);
    expect(screen.getByRole("textbox")).toHaveAttribute("type", "email");
  });

  it("passes placeholder through", () => {
    render(<Input placeholder="Enter email" />);
    expect(screen.getByPlaceholderText("Enter email")).toBeInTheDocument();
  });

  it("passes value and onChange through", async () => {
    const onChange = vi.fn();
    render(<Input value="hello" onChange={onChange} />);
    expect(screen.getByRole("textbox")).toHaveValue("hello");
  });

  it("calls onChange when user types", async () => {
    const onChange = vi.fn();
    render(<Input onChange={onChange} defaultValue="" />);
    await userEvent.type(screen.getByRole("textbox"), "a");
    expect(onChange).toHaveBeenCalled();
  });

  it("applies custom className", () => {
    render(<Input className="custom-class" />);
    expect(screen.getByRole("textbox")).toHaveClass("custom-class");
  });

  it("is disabled when disabled prop is set", () => {
    render(<Input disabled />);
    expect(screen.getByRole("textbox")).toBeDisabled();
  });

  it("forwards ref to the underlying input", () => {
    let ref: HTMLInputElement | null = null;
    render(<Input ref={(el) => { ref = el; }} />);
    expect(ref).toBeInstanceOf(HTMLInputElement);
  });
});
