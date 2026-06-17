// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuthFormError } from "@components/auth/forms/error";

describe("AuthFormError", () => {
  it("renders nothing when message is null", () => {
    const { container } = render(<AuthFormError message={null} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when message is undefined", () => {
    const { container } = render(<AuthFormError message={undefined} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders nothing when message is an empty string", () => {
    const { container } = render(<AuthFormError message="" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("renders the error message when present", () => {
    render(<AuthFormError message="Invalid credentials." />);
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials.");
  });

  it("uses role=alert so screen readers announce the error", () => {
    render(<AuthFormError message="Something went wrong." />);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });
});
