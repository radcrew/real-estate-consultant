// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BecomePartner } from "@components/landing/become-partner";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("BecomePartner", () => {
  it("renders the heading", () => {
    render(<BecomePartner />);
    expect(screen.getByRole("heading", { name: /list your property with raDestate/i })).toBeInTheDocument();
  });

  it("renders a link to the list-property page", () => {
    render(<BecomePartner />);
    expect(screen.getByRole("link", { name: /list your property/i })).toHaveAttribute(
      "href",
      "/list-property",
    );
  });

  it("renders the brand logo", () => {
    render(<BecomePartner />);
    expect(screen.getByText("RadEstate")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<BecomePartner className="mt-8" />);
    expect(container.firstChild).toHaveClass("mt-8");
  });
});
