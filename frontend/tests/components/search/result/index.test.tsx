// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { SearchResults } from "@components/search/result";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "prof-1" }),
}));
vi.mock("next/link", () => ({
  default: ({ href, children }: { href: string; children: React.ReactNode }) => <a href={href}>{children}</a>,
}));
vi.mock("next/image", () => ({
  default: ({ alt, src }: { alt: string; src: string }) => <img alt={alt} src={src} />,
}));
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ isSaved: () => false, toggle: vi.fn() }),
}));
vi.mock("@components/property/grid-with-map", () => ({
  SectionGridHasMap: () => <div data-testid="map-view" />,
}));
vi.mock("@components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children, "aria-label": al, disabled }: { children: React.ReactNode; "aria-label"?: string; disabled?: boolean }) => (
    <button aria-label={al} disabled={disabled}>{children}</button>
  ),
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuCheckboxItem: ({ children, checked, onCheckedChange }: { children: React.ReactNode; checked: boolean; onCheckedChange: (v: boolean) => void }) => (
    <label><input type="checkbox" checked={checked} onChange={(e) => onCheckedChange(e.target.checked)} />{children}</label>
  ),
}));
vi.mock("@components/ui/input", () => ({
  Input: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));
vi.mock("@hooks/use-location", () => ({
  useLocation: ({ initialQuery, onChange }: { initialQuery: string; onChange: (v: string) => void }) => ({
    query: initialQuery, suggestions: [], isLoadingSuggestions: false,
    loadError: null, showSuggestionList: false, placesHostRef: { current: null },
    handleQueryChange: onChange, selectSuggestion: vi.fn(),
  }),
}));

const mockUseSearchResults = vi.fn();
vi.mock("@hooks/use-search-results", () => ({
  useSearchResults: () => mockUseSearchResults(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockUseSearchResults.mockReturnValue({ models: [], loading: false, error: null, criteria: {}, applyCriteria: vi.fn() });
});

describe("SearchResults", () => {
  it("shows loading skeletons while loading", () => {
    mockUseSearchResults.mockReturnValue({ models: [], loading: true, error: null, criteria: {}, applyCriteria: vi.fn() });
    render(<SearchResults />);
    expect(screen.getByRole("status", { name: /loading search results/i })).toBeInTheDocument();
  });

  it("shows no-results notice when results are empty", () => {
    render(<SearchResults />);
    expect(screen.getByText(/no properties match/i)).toBeInTheDocument();
  });

  it("shows error message when error occurs", () => {
    mockUseSearchResults.mockReturnValue({ models: [], loading: false, error: "Search failed", criteria: {}, applyCriteria: vi.fn() });
    render(<SearchResults />);
    expect(screen.getByText("Search failed")).toBeInTheDocument();
  });

  it("shows result count label", () => {
    mockUseSearchResults.mockReturnValue({
      models: [
        { id: "p1", title: "W1", href: "/listings/p1", imageSrc: "", imageAlt: "", galleryImgs: [], category: "Warehouse",
          location: "Austin", transactionType: "For Lease", priceLabel: null, sqftLabel: "", matchScore: 0, matchBlurb: "",
          description: null, specs: [], map: null, mapsHref: null, broker: { name: null, email: null, phone: null } },
      ],
      loading: false, error: null, criteria: {}, applyCriteria: vi.fn(),
    });
    render(<SearchResults />);
    expect(screen.getByText("1 property")).toBeInTheDocument();
  });

  it("shows grid and map toggle buttons when results exist", () => {
    mockUseSearchResults.mockReturnValue({
      models: [
        { id: "p1", title: "W1", href: "/listings/p1", imageSrc: "", imageAlt: "", galleryImgs: [], category: "Warehouse",
          location: "Austin", transactionType: "For Lease", priceLabel: null, sqftLabel: "", matchScore: 0, matchBlurb: "",
          description: null, specs: [], map: null, mapsHref: null, broker: { name: null, email: null, phone: null } },
      ],
      loading: false, error: null, criteria: {}, applyCriteria: vi.fn(),
    });
    render(<SearchResults />);
    expect(screen.getByRole("button", { name: /grid/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /map/i })).toBeInTheDocument();
  });

  it("switches to map view when Map button clicked", () => {
    mockUseSearchResults.mockReturnValue({
      models: [
        { id: "p1", title: "W1", href: "/listings/p1", imageSrc: "", imageAlt: "", galleryImgs: [], category: "Warehouse",
          location: "Austin", transactionType: "For Lease", priceLabel: null, sqftLabel: "", matchScore: 0, matchBlurb: "",
          description: null, specs: [], map: null, mapsHref: null, broker: { name: null, email: null, phone: null } },
      ],
      loading: false, error: null, criteria: {}, applyCriteria: vi.fn(),
    });
    render(<SearchResults />);
    fireEvent.click(screen.getByRole("button", { name: /map/i }));
    expect(screen.getByTestId("map-view")).toBeInTheDocument();
  });
});
