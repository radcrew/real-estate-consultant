// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Testimonials } from "@components/landing/testimonials";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

describe("Testimonials", () => {
  it("renders the section heading", () => {
    render(<Testimonials />);
    expect(screen.getByRole("heading", { name: "What clients say" })).toBeInTheDocument();
  });

  it("renders all three testimonials", () => {
    render(<Testimonials />);
    expect(screen.getByText("Tiana Abie")).toBeInTheDocument();
    expect(screen.getByText("Lennie Swiffan")).toBeInTheDocument();
    expect(screen.getByText("Berta Emili")).toBeInTheDocument();
  });

  it("renders testimonial roles", () => {
    render(<Testimonials />);
    expect(screen.getByText("Tenant rep · Chicago")).toBeInTheDocument();
  });

  it("renders testimonial content as blockquotes", () => {
    render(<Testimonials />);
    expect(screen.getAllByRole("figure")).toHaveLength(3);
  });

  it("applies custom className", () => {
    const { container } = render(<Testimonials className="mt-8" />);
    expect(container.firstChild).toHaveClass("mt-8");
  });
});
