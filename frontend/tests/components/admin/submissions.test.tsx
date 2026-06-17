// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { AdminSubmissionsView } from "@components/admin/submissions";

const mockListSubmissions = vi.fn();
const mockUpdateSubmission = vi.fn();
vi.mock("@services/listings", () => ({
  listingsService: {
    listSubmissions: (...a: unknown[]) => mockListSubmissions(...a),
    updateSubmission: (...a: unknown[]) => mockUpdateSubmission(...a),
  },
}));

beforeEach(() => vi.clearAllMocks());

describe("AdminSubmissionsView", () => {
  it("shows loading while fetching", () => {
    mockListSubmissions.mockReturnValue(new Promise(() => {}));
    render(<AdminSubmissionsView />);
    expect(screen.getByText(/listing submissions/i)).toBeInTheDocument();
  });

  it("shows error on failure", async () => {
    mockListSubmissions.mockRejectedValue(new Error("Server error"));
    render(<AdminSubmissionsView />);
    await waitFor(() => expect(screen.getByText(/something went wrong/i)).toBeInTheDocument());
  });

  it("renders submissions after load", async () => {
    mockListSubmissions.mockResolvedValue([
      { id: "s1", title: "Warehouse A", city: "Austin", state: "TX", status: "pending", contact_name: "Bob", contact_email: "bob@test.com", property_type: "Warehouse", listing_type: "Lease", created_at: "2026-01-01" },
    ]);
    render(<AdminSubmissionsView />);
    await waitFor(() => expect(screen.getByText("Warehouse A")).toBeInTheDocument());
  });

  it("shows empty state when no submissions", async () => {
    mockListSubmissions.mockResolvedValue([]);
    render(<AdminSubmissionsView />);
    await waitFor(() => expect(screen.getByText(/no submissions/i)).toBeInTheDocument());
  });
});
