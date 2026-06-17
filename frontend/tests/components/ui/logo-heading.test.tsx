// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Logo } from "@components/ui/logo";
import { Heading2 } from "@components/ui/heading2";

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

describe("Logo", () => {
  it("renders a link to the home page", () => {
    render(<Logo />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/");
  });

  it("displays the brand name 'RadEstate'", () => {
    render(<Logo />);
    expect(screen.getByText("RadEstate")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<Logo className="text-xl" />);
    expect(screen.getByRole("link")).toHaveClass("text-xl");
  });
});

describe("Heading2", () => {
  it("renders a heading when provided", () => {
    render(<Heading2 heading="Browse listings" />);
    expect(screen.getByRole("heading", { name: "Browse listings" })).toBeInTheDocument();
  });

  it("does not render a heading element when heading is absent", () => {
    render(<Heading2 subHeading={<p>Sub</p>} />);
    expect(screen.queryByRole("heading")).not.toBeInTheDocument();
  });

  it("renders a sub-heading when provided", () => {
    render(<Heading2 subHeading={<p>Sub text</p>} />);
    expect(screen.getByText("Sub text")).toBeInTheDocument();
  });

  it("applies custom className to the wrapper", () => {
    const { container } = render(<Heading2 className="mt-8" />);
    expect(container.firstChild).toHaveClass("mt-8");
  });
});
