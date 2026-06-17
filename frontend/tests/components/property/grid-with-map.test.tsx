// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SectionGridHasMap } from "@components/property/grid-with-map";
import type { PropertyModel } from "@typings/property";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));
vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ isSaved: () => false, toggle: vi.fn() }),
}));
vi.mock("@components/property/map", () => ({
  PropertyMap: ({ items }: { items: unknown[] }) => <div data-testid="map" data-count={items.length} />,
}));

const MODEL: PropertyModel = {
  id: "p1", title: "W1", href: "/listings/p1", imageSrc: "", imageAlt: "W1",
  galleryImgs: [], category: "Warehouse", location: "Austin, TX",
  transactionType: "For Lease", priceLabel: null, sqftLabel: "5,000 SF",
  matchScore: 0, matchBlurb: "", description: null, specs: [],
  map: { lat: 30.25, lng: -97.75 }, mapsHref: null,
  broker: { name: null, email: null, phone: null },
};

describe("SectionGridHasMap", () => {
  it("renders the property map", () => {
    render(<SectionGridHasMap data={[MODEL]} />);
    expect(screen.getByTestId("map")).toBeInTheDocument();
  });

  it("renders a card for each item", () => {
    render(<SectionGridHasMap data={[MODEL]} />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/listings/p1");
  });

  it("renders optional heading when provided", () => {
    render(<SectionGridHasMap data={[]} heading="Results" />);
    expect(screen.getByText("Results")).toBeInTheDocument();
  });

  it("renders nothing extra when data is empty", () => {
    const { container } = render(<SectionGridHasMap data={[]} />);
    expect(container.querySelectorAll("a").length).toBe(0);
  });
});
