// @vitest-environment jsdom
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ListingActions } from "@components/listings/detail/actions";

const mockIsSaved = vi.fn();
const mockToggle = vi.fn();
vi.mock("@components/saved/provider", () => ({
  useSavedListings: () => ({ isSaved: mockIsSaved, toggle: mockToggle }),
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockIsSaved.mockReturnValue(false);
});

describe("ListingActions", () => {
  it("renders the Save button when not saved", () => {
    render(<ListingActions id="p1" />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByText("Save")).toBeInTheDocument();
  });

  it("renders Saved when already saved", () => {
    mockIsSaved.mockReturnValue(true);
    render(<ListingActions id="p1" />);
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("calls toggle when button clicked", () => {
    render(<ListingActions id="p1" />);
    fireEvent.click(screen.getByRole("button"));
    expect(mockToggle).toHaveBeenCalledWith("p1");
  });

  it("does not call toggle when id is absent", () => {
    render(<ListingActions />);
    fireEvent.click(screen.getByRole("button"));
    expect(mockToggle).not.toHaveBeenCalled();
  });
});
