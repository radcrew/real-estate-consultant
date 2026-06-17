// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SearchFilter } from "@components/search/result/filter-bar";

vi.mock("@components/ui/dropdown-menu", () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children, "aria-label": ariaLabel, disabled }: { children: React.ReactNode; "aria-label"?: string; disabled?: boolean }) => (
    <button aria-label={ariaLabel} disabled={disabled}>{children}</button>
  ),
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuCheckboxItem: ({ children, checked, onCheckedChange }: { children: React.ReactNode; checked: boolean; onCheckedChange: (v: boolean) => void }) => (
    <label>
      <input type="checkbox" checked={checked} onChange={(e) => onCheckedChange(e.target.checked)} />
      {children}
    </label>
  ),
}));

vi.mock("@components/ui/input", () => ({
  Input: ({ id, value, onChange, ...rest }: React.InputHTMLAttributes<HTMLInputElement>) => (
    <input id={id} value={value} onChange={onChange} {...rest} />
  ),
}));

vi.mock("@hooks/use-location", () => ({
  useLocation: ({ initialQuery, onChange }: { initialQuery: string; onChange: (v: string) => void }) => ({
    query: initialQuery,
    suggestions: [],
    isLoadingSuggestions: false,
    loadError: null,
    showSuggestionList: false,
    placesHostRef: { current: null },
    handleQueryChange: onChange,
    selectSuggestion: vi.fn(),
  }),
}));

const MULTI_CRITERIA = {
  propertyType: {
    type: "multi-select",
    label: "Property Type",
    data: [],
  },
};

const RANGE_CRITERIA = {
  sqft: {
    type: "range",
    label: "Sqft",
    unit: "sqft",
    data: { min: Number.NaN, max: Number.NaN },
  },
};

describe("SearchFilter", () => {
  it("renders nothing when criteria is empty", () => {
    const { container } = render(<SearchFilter criteria={{}} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders a multi-select filter trigger", () => {
    render(<SearchFilter criteria={MULTI_CRITERIA} />);
    expect(screen.getByRole("button", { name: /property type/i })).toBeInTheDocument();
  });

  it("renders a range filter trigger", () => {
    render(<SearchFilter criteria={RANGE_CRITERIA} />);
    expect(screen.getByRole("button", { name: /sqft/i })).toBeInTheDocument();
  });

  it("renders Clear and Search buttons", () => {
    const onSearch = vi.fn();
    render(<SearchFilter criteria={RANGE_CRITERIA} onSearch={onSearch} />);
    expect(screen.getByRole("button", { name: "Clear" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
  });

  it("calls onSearch with updated criteria when Search is clicked", () => {
    const onSearch = vi.fn();
    render(<SearchFilter criteria={RANGE_CRITERIA} onSearch={onSearch} />);
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    expect(onSearch).toHaveBeenCalledTimes(1);
  });

  it("disables buttons when disabled prop is set", () => {
    render(<SearchFilter criteria={RANGE_CRITERIA} disabled />);
    expect(screen.getByRole("button", { name: "Clear" })).toBeDisabled();
  });
});
