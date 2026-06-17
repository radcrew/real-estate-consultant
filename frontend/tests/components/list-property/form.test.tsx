// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { ListPropertyForm } from "@components/list-property/form";

const mockSubmitListing = vi.fn();
vi.mock("@services/listings", () => ({
  listingsService: { submitListing: (...a: unknown[]) => mockSubmitListing(...a) },
}));

beforeEach(() => vi.clearAllMocks());

describe("ListPropertyForm", () => {
  it("renders the form with a submit button", () => {
    render(<ListPropertyForm />);
    expect(screen.getByRole("button", { name: /submit listing/i })).toBeInTheDocument();
  });

  it("renders the listing contact section", () => {
    render(<ListPropertyForm />);
    expect(screen.getByText("Listing contact")).toBeInTheDocument();
  });

  it("shows success message after submit", async () => {
    mockSubmitListing.mockResolvedValue({ id: "sub-1", status: "pending" });
    render(<ListPropertyForm />);
    fireEvent.submit(screen.getByRole("button", { name: /submit listing/i }).closest("form")!);
    await waitFor(() => expect(screen.getByText(/submitted/i)).toBeInTheDocument());
  });

  it("shows error message on failure", async () => {
    mockSubmitListing.mockRejectedValue(new Error("Server error"));
    render(<ListPropertyForm />);
    fireEvent.submit(screen.getByRole("button", { name: /submit listing/i }).closest("form")!);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
  });
});
