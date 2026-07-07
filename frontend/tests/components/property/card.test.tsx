// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { PropertyCard, PropertyCardSkeleton } from "@components/property/card";
import type { PropertyModel } from "@typings/property";
import type { FitExplanation } from "@services/search";

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

describe("PropertyCard fit explanation", () => {
  const EXPLANATION: FitExplanation = {
    property_id: "p-1",
    score: { location: 1, price: 0.8, size: 0.6, total: 82 },
    summary: "This listing is right in your target city.",
    strengths: ["Right city", "Close to target price"],
    considerations: ["Slightly larger than requested"],
  };

  it("does not render the affordance without onExplainFit", () => {
    render(<PropertyCard data={MODEL} />);
    expect(screen.queryByText(/why this fits/i)).not.toBeInTheDocument();
  });

  it("does not render the affordance when matchScore is 0", () => {
    render(<PropertyCard data={{ ...MODEL, matchScore: 0 }} onExplainFit={vi.fn()} />);
    expect(screen.queryByText(/why this fits/i)).not.toBeInTheDocument();
  });

  it("calls onExplainFit when expanded for the first time", () => {
    const onExplainFit = vi.fn();
    render(<PropertyCard data={MODEL} onExplainFit={onExplainFit} />);
    fireEvent.click(screen.getByText(/why this fits/i));
    expect(onExplainFit).toHaveBeenCalledTimes(1);
  });

  it("does not navigate via the surrounding link when clicked", () => {
    const onExplainFit = vi.fn();
    render(<PropertyCard data={MODEL} onExplainFit={onExplainFit} />);
    const event = fireEvent.click(screen.getByText(/why this fits/i));
    expect(event).toBe(false); // preventDefault() was called
  });

  it("shows a loading state while generating", () => {
    render(<PropertyCard data={MODEL} onExplainFit={vi.fn()} fitLoading />);
    fireEvent.click(screen.getByText(/why this fits/i));
    expect(screen.getByText(/explaining/i)).toBeInTheDocument();
  });

  it("renders the summary, strengths, and considerations once available", () => {
    render(
      <PropertyCard data={MODEL} onExplainFit={vi.fn()} fitExplanation={EXPLANATION} />,
    );
    fireEvent.click(screen.getByText(/why this fits/i));
    expect(screen.getByText(EXPLANATION.summary)).toBeInTheDocument();
    expect(screen.getByText("Right city")).toBeInTheDocument();
    expect(screen.getByText("Slightly larger than requested")).toBeInTheDocument();
  });

  it("does not re-call onExplainFit once a cached explanation exists", () => {
    const onExplainFit = vi.fn();
    render(
      <PropertyCard
        data={MODEL}
        onExplainFit={onExplainFit}
        fitExplanation={EXPLANATION}
      />,
    );
    fireEvent.click(screen.getByText(/why this fits/i));
    expect(onExplainFit).not.toHaveBeenCalled();
  });

  it("toggles the panel closed on a second click", () => {
    render(
      <PropertyCard data={MODEL} onExplainFit={vi.fn()} fitExplanation={EXPLANATION} />,
    );
    fireEvent.click(screen.getByText(/why this fits/i));
    expect(screen.getByText(EXPLANATION.summary)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/hide why this fits/i));
    expect(screen.queryByText(EXPLANATION.summary)).not.toBeInTheDocument();
  });
});

describe("PropertyCardSkeleton", () => {
  it("renders a loading placeholder", () => {
    const { container } = render(<PropertyCardSkeleton />);
    expect(container.firstChild).toBeInTheDocument();
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
