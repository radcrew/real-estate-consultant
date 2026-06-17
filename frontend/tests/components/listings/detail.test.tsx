// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ListingOverviewCard } from "@components/listings/detail/overview";
import { ListingSpecsSection } from "@components/listings/detail/specs";
import { ListingDetailNotice, ListingDetailSkeleton } from "@components/listings/detail/status";
import { ListingLocationSection } from "@components/listings/detail/location";
import type { ListingProperty } from "@services/listings";

vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock("@components/property/map", () => ({
  PropertyMap: () => <div data-testid="property-map" />,
}));

const BASE_PROPERTY: ListingProperty = {
  id: "p1",
  name: "Warehouse A",
  address: "1 Commerce Way",
  city: "Austin",
  state: "TX",
  country: "US",
  property_type: "Warehouse",
  listing_type: "For Lease",
  size_sqft: 20000,
  price: null,
  rent: 12,
  clear_height: 24,
  loading_docks: 4,
  description: "Large warehouse near highway.",
  listing_broker_name: "Jane Broker",
  listing_broker_email: "jane@broker.com",
  listing_broker_phone: "512-555-1234",
  lat: 30.25,
  lng: -97.75,
};

const BASE_MODEL = {
  id: "p1",
  title: "Warehouse A",
  href: "/listings/p1",
  imageSrc: "/img.jpg",
  imageAlt: "Warehouse A",
  galleryImgs: [],
  category: "Warehouse",
  location: "Austin, TX",
  transactionType: "For Lease",
  priceLabel: null,
  sqftLabel: "20,000 sqft",
  matchScore: 0,
  matchBlurb: "",
  description: "Large warehouse.",
  specs: [],
  map: { lat: 30.25, lng: -97.75 },
  mapsHref: null,
  broker: { name: "Jane Broker", email: null, phone: null },
};

describe("ListingOverviewCard", () => {
  it("renders the overview heading", () => {
    render(<ListingOverviewCard property={BASE_PROPERTY} />);
    expect(screen.getByText("Overview")).toBeInTheDocument();
  });

  it("renders the broker name as a link", () => {
    render(<ListingOverviewCard property={BASE_PROPERTY} />);
    expect(screen.getByRole("link", { name: "Jane Broker" })).toBeInTheDocument();
  });

  it("renders the broker email", () => {
    render(<ListingOverviewCard property={BASE_PROPERTY} />);
    expect(screen.getByText("jane@broker.com")).toBeInTheDocument();
  });

  it("renders loading docks count", () => {
    render(<ListingOverviewCard property={BASE_PROPERTY} />);
    expect(screen.getByText("4")).toBeInTheDocument();
  });
});

describe("ListingSpecsSection", () => {
  it("renders property specifications heading", () => {
    render(<ListingSpecsSection property={BASE_PROPERTY} />);
    expect(screen.getByRole("heading", { name: /property specifications/i })).toBeInTheDocument();
  });

  it("renders property type spec", () => {
    render(<ListingSpecsSection property={BASE_PROPERTY} />);
    expect(screen.getByText("Warehouse")).toBeInTheDocument();
  });

  it("returns null when no specs exist", () => {
    const empty: ListingProperty = { ...BASE_PROPERTY, property_type: null, listing_type: null, size_sqft: null, clear_height: null, loading_docks: null };
    const { container } = render(<ListingSpecsSection property={empty} />);
    expect(container.firstChild).toBeNull();
  });
});

describe("ListingDetailNotice", () => {
  it("renders the message", () => {
    render(<ListingDetailNotice message="Listing not found." />);
    expect(screen.getByText("Listing not found.")).toBeInTheDocument();
  });

  it("renders the title when provided", () => {
    render(<ListingDetailNotice title="Error" message="Something went wrong." tone="error" />);
    expect(screen.getByRole("heading", { name: "Error" })).toBeInTheDocument();
  });

  it("renders an action slot", () => {
    render(<ListingDetailNotice message="Empty." action={<a href="/">Go home</a>} />);
    expect(screen.getByRole("link", { name: "Go home" })).toBeInTheDocument();
  });
});

describe("ListingDetailSkeleton", () => {
  it("renders animated skeleton elements", () => {
    const { container } = render(<ListingDetailSkeleton />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});

describe("ListingLocationSection", () => {
  it("renders the map when coordinates are present", () => {
    render(<ListingLocationSection model={BASE_MODEL as never} />);
    expect(screen.getByTestId("property-map")).toBeInTheDocument();
  });

  it("returns null when model has no map", () => {
    const { container } = render(<ListingLocationSection model={{ ...BASE_MODEL, map: null } as never} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders the location label", () => {
    render(<ListingLocationSection model={BASE_MODEL as never} />);
    expect(screen.getByText("Austin, TX")).toBeInTheDocument();
  });
});
