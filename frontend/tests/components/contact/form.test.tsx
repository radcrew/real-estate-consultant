// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ContactForm } from "@components/contact/form";

describe("ContactForm", () => {
  it("renders the form with all fields", () => {
    render(<ContactForm />);
    expect(screen.getByPlaceholderText("Example Doe")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("example@example.com")).toBeInTheDocument();
  });

  it("renders a submit button", () => {
    render(<ContactForm />);
    expect(screen.getByRole("button", { name: /send message/i })).toBeInTheDocument();
  });

  it("shows a confirmation message after submit", async () => {
    render(<ContactForm />);
    // Submit via fireEvent to bypass native required validation
    const form = screen.getByRole("button", { name: /send message/i }).closest("form")!;
    const { fireEvent } = await import("@testing-library/react");
    fireEvent.submit(form);
    expect(await screen.findByRole("status")).toHaveTextContent(
      /thanks for reaching out/i,
    );
  });

  it("hides the form after submit", async () => {
    render(<ContactForm />);
    const form = screen.getByRole("button").closest("form")!;
    const { fireEvent } = await import("@testing-library/react");
    fireEvent.submit(form);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
