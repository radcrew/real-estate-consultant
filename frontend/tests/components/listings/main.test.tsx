// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ListingMainSection } from "@components/listings/detail/main";
import type { ListingProperty } from "@services/listings";

const PROPERTY: ListingProperty = {
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
  clear_height: null,
  loading_docks: null,
  description: "A great industrial warehouse.",
  listing_broker_name: null,
  listing_broker_email: null,
  listing_broker_phone: null,
  lat: null,
  lng: null,
  latitude: 30.25,
  longitude: -97.75,
};

describe("ListingMainSection", () => {
  it("renders the property title", () => {
    render(<ListingMainSection property={PROPERTY} />);
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("renders property type badge", () => {
    render(<ListingMainSection property={PROPERTY} />);
    expect(screen.getByText("Warehouse")).toBeInTheDocument();
  });

  it("renders listing type badge", () => {
    render(<ListingMainSection property={PROPERTY} />);
    expect(screen.getByText("For Lease")).toBeInTheDocument();
  });

  it("renders the description", () => {
    render(<ListingMainSection property={PROPERTY} />);
    expect(screen.getByText("A great industrial warehouse.")).toBeInTheDocument();
  });

  it("renders Google Maps link when coordinates present", () => {
    render(<ListingMainSection property={PROPERTY} />);
    expect(screen.getByRole("link", { name: /google maps/i })).toBeInTheDocument();
  });

  it("does not render description section when absent", () => {
    render(<ListingMainSection property={{ ...PROPERTY, description: null }} />);
    expect(screen.queryByText(/property description/i)).not.toBeInTheDocument();
  });
});
