// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Badge } from "@components/ui/badge";

vi.mock("next/link", () => ({
  default: ({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) => (
    <a href={href} className={className}>{children}</a>
  ),
}));

describe("Badge", () => {
  it("renders as a span when no href is given", () => {
    render(<Badge name="Warehouse" />);
    const badge = screen.getByText("Warehouse");
    expect(badge.tagName).toBe("SPAN");
  });

  it("renders as a link when href is provided", () => {
    render(<Badge name="Office" href="/search?type=office" />);
    expect(screen.getByRole("link", { name: "Office" })).toHaveAttribute(
      "href",
      "/search?type=office",
    );
  });

  it("renders the name content", () => {
    render(<Badge name="Industrial" />);
    expect(screen.getByText("Industrial")).toBeInTheDocument();
  });

  it("applies the default blue color classes", () => {
    render(<Badge name="Blue" />);
    expect(screen.getByText("Blue")).toHaveClass("text-blue-800", "bg-blue-100");
  });

  it("applies the correct classes for other colors", () => {
    render(<Badge name="Green" color="green" />);
    expect(screen.getByText("Green")).toHaveClass("text-green-800", "bg-green-100");
  });

  it("applies extra className when provided", () => {
    render(<Badge name="Extra" className="my-2" />);
    expect(screen.getByText("Extra")).toHaveClass("my-2");
  });

  it("accepts ReactNode as name", () => {
    render(<Badge name={<strong>Bold</strong>} />);
    expect(screen.getByText("Bold").tagName).toBe("STRONG");
  });
});
