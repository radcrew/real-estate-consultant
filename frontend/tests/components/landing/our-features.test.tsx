// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OurFeatures } from "@components/landing/our-features";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("OurFeatures", () => {
  it("renders the main heading", () => {
    render(<OurFeatures />);
    expect(screen.getByRole("heading", { name: /built for cre professionals/i })).toBeInTheDocument();
  });

  it("renders all three feature titles", () => {
    render(<OurFeatures />);
    expect(screen.getByText("AI fit scoring")).toBeInTheDocument();
    expect(screen.getByText("Search the whole market")).toBeInTheDocument();
    expect(screen.getByText("Secure and simple")).toBeInTheDocument();
  });

  it("renders feature badge labels", () => {
    render(<OurFeatures />);
    expect(screen.getByText("Scoring")).toBeInTheDocument();
    expect(screen.getByText("Coverage")).toBeInTheDocument();
    expect(screen.getByText("Outreach")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<OurFeatures className="mt-12" />);
    expect(container.firstChild).toHaveClass("mt-12");
  });
});
