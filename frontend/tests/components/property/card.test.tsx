// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PropertyCard, PropertyCardSkeleton } from "@components/property/card";
import type { PropertyModel } from "@typings/property";

vi.mock("next/image", () => ({
  default: ({ alt, src, onError }: { alt: string; src: string; onError?: () => void }) => (
    <img alt={alt} src={src} onError={onError} />
  ),
}));

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ isSaved: () => false, toggle: vi.fn() }),
}));

const MODEL: PropertyModel = {
  id: "p-1",
  title: "Downtown Warehouse",
  href: "/listings/p-1",
  imageSrc: "/images/warehouse.jpg",
  imageAlt: "Downtown Warehouse",
  galleryImgs: [],
  category: "Warehouse",
  location: "Austin, TX",
  transactionType: "For Lease",
  priceLabel: "$12/sqft/yr",
  sqftLabel: "10,000 sqft",
  matchScore: 92,
  matchBlurb: "Strong match",
  description: "A great warehouse.",
  specs: [],
  map: null,
  mapsHref: null,
  broker: { name: "Jane Doe", email: null, phone: null },
};

describe("PropertyCard", () => {
  it("renders the listing title", () => {
    render(<PropertyCard data={MODEL} />);
    expect(screen.getByText("Downtown Warehouse")).toBeInTheDocument();
  });

  it("links to the correct listing href", () => {
    render(<PropertyCard data={MODEL} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/listings/p-1");
  });

  it("renders the price label", () => {
    render(<PropertyCard data={MODEL} />);
    expect(screen.getByText("$12/sqft/yr")).toBeInTheDocument();
  });

  it("renders the category badge", () => {
    render(<PropertyCard data={MODEL} />);
    expect(screen.getByText("Warehouse")).toBeInTheDocument();
  });

  it("renders the location", () => {
    render(<PropertyCard data={MODEL} />);
    expect(screen.getByText(/Austin/)).toBeInTheDocument();
  });
});

describe("PropertyCardSkeleton", () => {
  it("renders a loading placeholder", () => {
    const { container } = render(<PropertyCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
