// @vitest-environment jsdom
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { SidePanel } from "@components/search/wizard/modes/llm/panels/side";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

const mockWizard = vi.fn();
vi.mock("@contexts/search-wizard", () => ({
  useSearchWizard: () => mockWizard(),
}));

const mockCompleteSession = vi.fn();
vi.mock("@services/intake-sessions", () => ({
  intakeSessionsService: { completeSession: (...a: unknown[]) => mockCompleteSession(...a) },
}));

beforeEach(() => {
  vi.clearAllMocks();
  mockWizard.mockReturnValue({
    sessionId: "sess-1",
    setErrorMessage: vi.fn(),
    resetToChooser: vi.fn(),
    onClose: vi.fn(),
  });
});

describe("SidePanel", () => {
  it("renders empty-criteria message when no criteria", () => {
    render(<SidePanel lastResponse={null} />);
    expect(screen.getByText(/criteria will appear/i)).toBeInTheDocument();
  });

  it("renders extracted criteria", () => {
    render(
      <SidePanel
        lastResponse={{ criteria: { location: "Austin" }, missing_fields: [], question_titles: {} } as never}
      />,
    );
    expect(screen.getByText("Austin")).toBeInTheDocument();
  });

  it("renders missing fields as optional details", () => {
    render(
      <SidePanel
        lastResponse={{ criteria: {}, missing_fields: ["size_sqft"], question_titles: { size_sqft: "Building size" } } as never}
      />,
    );
    expect(screen.getByText("Building size")).toBeInTheDocument();
  });

  it("calls resetToChooser when Switch mode clicked", () => {
    const resetToChooser = vi.fn();
    mockWizard.mockReturnValue({ sessionId: "s1", setErrorMessage: vi.fn(), resetToChooser, onClose: vi.fn() });
    render(<SidePanel lastResponse={null} />);
    fireEvent.click(screen.getByRole("button", { name: /switch mode/i }));
    expect(resetToChooser).toHaveBeenCalledTimes(1);
  });

  it("navigates to search results after completing session", async () => {
    mockCompleteSession.mockResolvedValue({ search_profile_id: "prof-99" });
    render(<SidePanel lastResponse={null} />);
    fireEvent.click(screen.getByRole("button", { name: /search properties/i }));
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/search/prof-99"));
  });
});
