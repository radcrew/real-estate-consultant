// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Select } from "@components/ui/select";

describe("Select", () => {
  it("renders a select element", () => {
    render(
      <Select aria-label="Type">
        <option value="a">Option A</option>
      </Select>,
    );
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("renders children as options", () => {
    render(
      <Select aria-label="Type">
        <option value="warehouse">Warehouse</option>
        <option value="office">Office</option>
      </Select>,
    );
    expect(screen.getByRole("option", { name: "Warehouse" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "Office" })).toBeInTheDocument();
  });

  it("calls onChange when an option is selected", async () => {
    const onChange = vi.fn();
    render(
      <Select aria-label="Type" onChange={onChange}>
        <option value="warehouse">Warehouse</option>
        <option value="office">Office</option>
      </Select>,
    );
    await userEvent.selectOptions(screen.getByRole("combobox"), "office");
    expect(onChange).toHaveBeenCalled();
  });

  it("applies custom className", () => {
    render(<Select aria-label="Type" className="w-full" />);
    expect(screen.getByRole("combobox")).toHaveClass("w-full");
  });

  it("is disabled when disabled prop is set", () => {
    render(<Select aria-label="Type" disabled />);
    expect(screen.getByRole("combobox")).toBeDisabled();
  });

  it("forwards ref to the underlying select", () => {
    let ref: HTMLSelectElement | null = null;
    render(<Select aria-label="Type" ref={(el) => { ref = el; }} />);
    expect(ref).toBeInstanceOf(HTMLSelectElement);
  });
});
