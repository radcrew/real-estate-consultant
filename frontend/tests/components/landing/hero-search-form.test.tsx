// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { HeroRealEstateSearchForm } from "@components/landing/hero/search-form";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push: mockPush }) }));

vi.mock("@components/landing/hero/search-form/location-input", () => ({
  LocationInput: ({ value, onChange }: { value: string; onChange: (v: string) => void }) => (
    <input aria-label="Location" value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));
vi.mock("@components/landing/hero/search-form/property-type-select", () => ({
  DEFAULT_PROPERTY_TYPES: [{ name: "Warehouse", checked: true }],
  PropertyTypeSelect: () => <div data-testid="type-select" />,
}));
const mockQuickSearch = vi.fn();
vi.mock("@services/search", () => ({
  searchService: { quickSearch: (...a: unknown[]) => mockQuickSearch(...a) },
}));

beforeEach(() => vi.clearAllMocks());

describe("HeroRealEstateSearchForm", () => {
  it("renders the location input", () => {
    render(<HeroRealEstateSearchForm />);
    expect(screen.getByRole("textbox", { name: /location/i })).toBeInTheDocument();
  });

  it("renders the property type selector", () => {
    render(<HeroRealEstateSearchForm />);
    expect(screen.getByTestId("type-select")).toBeInTheDocument();
  });

  it("renders the search button", () => {
    render(<HeroRealEstateSearchForm />);
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("navigates to search results on submit", async () => {
    mockQuickSearch.mockResolvedValue({ search_profile_id: "prof-42" });
    render(<HeroRealEstateSearchForm />);
    fireEvent.click(screen.getByRole("button", { name: /search/i }));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/search/prof-42"));
  });

  it("submits only once per click (button click + native form submit must not double-fire)", async () => {
    mockQuickSearch.mockResolvedValue({ search_profile_id: "prof-42" });
    render(<HeroRealEstateSearchForm />);
    fireEvent.click(screen.getByRole("button", { name: /search/i }));
    await waitFor(() => expect(mockQuickSearch).toHaveBeenCalledTimes(1));
  });
});
