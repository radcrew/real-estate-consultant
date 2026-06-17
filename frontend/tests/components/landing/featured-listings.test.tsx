// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { FeaturedListings } from "@components/landing/featured-listings";

vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));
vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ isSaved: () => false, toggle: vi.fn() }),
}));

const mockGetFeatured = vi.fn();
vi.mock("@services/listings", () => ({
  listingsService: { getFeaturedListings: (...a: unknown[]) => mockGetFeatured(...a) },
}));

beforeEach(() => vi.clearAllMocks());

describe("FeaturedListings", () => {
  it("renders skeletons while loading", () => {
    mockGetFeatured.mockReturnValue(new Promise(() => {}));
    const { container } = render(<FeaturedListings />);
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("renders property cards after load", async () => {
    mockGetFeatured.mockResolvedValue({
      listings: [
        {
          property: {
            id: "1", name: "Warehouse A", address: "1 Main", city: "Austin", state: "TX", country: "US",
            property_type: "Warehouse", listing_type: "For Lease", size_sqft: 5000,
            price: null, rent: 10, clear_height: null, loading_docks: null,
            description: null, listing_broker_name: null, listing_broker_email: null,
            listing_broker_phone: null, lat: null, lng: null, latitude: null, longitude: null,
            image: null,
          },
          images: [],
        },
      ],
    });
    render(<FeaturedListings />);
    await waitFor(() => expect(screen.getByText("5,000 SF")).toBeInTheDocument());
  });

  it("renders browse link", async () => {
    mockGetFeatured.mockResolvedValue({ listings: [] });
    render(<FeaturedListings />);
    await waitFor(() => expect(screen.getByRole("link", { name: /browse properties/i })).toHaveAttribute("href", "/listings"));
  });
});
