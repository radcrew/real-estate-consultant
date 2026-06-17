// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Checkbox } from "@components/ui/checkbox";

describe("Checkbox", () => {
  it("renders a checkbox input", () => {
    render(<Checkbox name="agree" />);
    expect(screen.getByRole("checkbox")).toBeInTheDocument();
  });

  it("is unchecked by default", () => {
    render(<Checkbox name="agree" />);
    expect(screen.getByRole("checkbox")).not.toBeChecked();
  });

  it("is checked when defaultChecked is true", () => {
    render(<Checkbox name="agree" defaultChecked />);
    expect(screen.getByRole("checkbox")).toBeChecked();
  });

  it("renders a label when label prop is provided", () => {
    render(<Checkbox name="agree" label="I agree" />);
    expect(screen.getByLabelText("I agree")).toBeInTheDocument();
  });

  it("does not render a label element when label is omitted", () => {
    render(<Checkbox name="agree" />);
    expect(screen.queryByRole("label")).not.toBeInTheDocument();
  });

  it("renders a sub-label when provided", () => {
    render(<Checkbox name="agree" label="I agree" subLabel="Terms and conditions" />);
    expect(screen.getByText("Terms and conditions")).toBeInTheDocument();
  });

  it("does not render sub-label when omitted", () => {
    render(<Checkbox name="agree" label="I agree" />);
    expect(screen.queryByText("Terms and conditions")).not.toBeInTheDocument();
  });

  it("calls onChange with true when checked", async () => {
    const onChange = vi.fn();
    render(<Checkbox name="agree" onChange={onChange} />);
    await userEvent.click(screen.getByRole("checkbox"));
    expect(onChange).toHaveBeenCalledWith(true);
  });

  it("calls onChange with false when unchecked", async () => {
    const onChange = vi.fn();
    render(<Checkbox name="agree" defaultChecked onChange={onChange} />);
    await userEvent.click(screen.getByRole("checkbox"));
    expect(onChange).toHaveBeenCalledWith(false);
  });

  it("associates label with checkbox via htmlFor/id", () => {
    render(<Checkbox name="terms" label="Accept terms" />);
    expect(screen.getByLabelText("Accept terms")).toHaveAttribute("id", "terms");
  });
});
