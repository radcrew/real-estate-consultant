// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CategorySlider } from "@components/landing/category-slider";
import type { Category } from "@components/landing/category-slider/data";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

vi.mock("@services/search", () => ({
  searchService: { quickSearch: vi.fn() },
}));

vi.mock("embla-carousel-react", () => ({
  default: () => [vi.fn(), undefined],
}));

const CATS: Category[] = [
  { id: "1", name: "Office", thumbnail: "/office.jpg", search: { propertyType: "office" } },
  { id: "2", name: "Industrial", thumbnail: "/industrial.jpg", search: { propertyType: "industrial" } },
];

describe("CategorySlider", () => {
  it("renders the heading", () => {
    render(
      <CategorySlider
        heading="Browse by type"
        subHeading="Find your space"
        categories={CATS}
        cardType="card4"
        slideClassName="w-1/3"
      />,
    );
    expect(screen.getByText("Browse by type")).toBeInTheDocument();
  });

  it("renders a card for each category", () => {
    render(
      <CategorySlider
        heading="Browse by type"
        subHeading="Find your space"
        categories={CATS}
        cardType="card4"
        slideClassName="w-1/3"
      />,
    );
    expect(screen.getByRole("heading", { name: "Office" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Industrial" })).toBeInTheDocument();
  });

  it("renders prev/next navigation buttons", () => {
    render(
      <CategorySlider
        heading="Browse by type"
        subHeading="Find your space"
        categories={CATS}
        cardType="card4"
        slideClassName="w-1/3"
      />,
    );
    expect(screen.getAllByRole("button", { name: /prev/i }).length).toBeGreaterThan(0);
    expect(screen.getAllByRole("button", { name: /next/i }).length).toBeGreaterThan(0);
  });
});
