// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ButtonClose } from "@components/ui/button-close";

describe("ButtonClose", () => {
  it("renders a button", () => {
    render(<ButtonClose />);
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("has an accessible 'Close' label for screen readers", () => {
    render(<ButtonClose />);
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const onClick = vi.fn();
    render(<ButtonClose onClick={onClick} />);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("applies custom className", () => {
    render(<ButtonClose className="absolute top-2 right-2" />);
    expect(screen.getByRole("button")).toHaveClass("absolute", "top-2", "right-2");
  });

  it("renders the X icon", () => {
    const { container } = render(<ButtonClose />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });
});
