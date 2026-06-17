// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SectionHero } from "@components/landing/hero";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@components/landing/hero/search-form", () => ({
  HeroRealEstateSearchForm: () => <div data-testid="search-form" />,
}));

describe("SectionHero", () => {
  it("renders the hero heading from brand config", () => {
    render(<SectionHero />);
    expect(
      screen.getByRole("heading", { name: /find your next commercial property/i }),
    ).toBeInTheDocument();
  });

  it("renders the primary CTA link", () => {
    render(<SectionHero />);
    expect(screen.getByRole("link", { name: /start searching/i })).toHaveAttribute(
      "href",
      "/questionnaire",
    );
  });

  it("renders the hero image", () => {
    render(<SectionHero />);
    expect(screen.getByAltText("Commercial real estate")).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<SectionHero className="mt-4" />);
    expect(container.firstChild).toHaveClass("mt-4");
  });
});
