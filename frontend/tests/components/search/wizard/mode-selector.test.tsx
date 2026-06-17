// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SearchModeSelector } from "@components/search/wizard/modes/selector";

const mockWizard = {
  errorMessage: null as string | null,
  isBusy: false,
  onClose: vi.fn(),
  startSmartChat: vi.fn(),
  startGuidedForm: vi.fn(),
};

vi.mock("@contexts/search-wizard", () => ({
  useSearchWizard: () => mockWizard,
}));

beforeEach(() => {
  mockWizard.errorMessage = null;
  mockWizard.isBusy = false;
  mockWizard.onClose = vi.fn();
  mockWizard.startSmartChat = vi.fn();
  mockWizard.startGuidedForm = vi.fn();
});

describe("SearchModeSelector", () => {
  it("renders the heading", () => {
    render(<SearchModeSelector />);
    expect(screen.getByRole("heading", { name: /how would you like to search/i })).toBeInTheDocument();
  });

  it("renders Use Form and Use AI Chat buttons", () => {
    render(<SearchModeSelector />);
    expect(screen.getByRole("button", { name: /use form/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /use ai chat/i })).toBeInTheDocument();
  });

  it("calls startGuidedForm when Use Form is clicked", async () => {
    render(<SearchModeSelector />);
    await userEvent.click(screen.getByRole("button", { name: /use form/i }));
    expect(mockWizard.startGuidedForm).toHaveBeenCalledOnce();
  });

  it("calls startSmartChat when Use AI Chat is clicked", async () => {
    render(<SearchModeSelector />);
    await userEvent.click(screen.getByRole("button", { name: /use ai chat/i }));
    expect(mockWizard.startSmartChat).toHaveBeenCalledOnce();
  });

  it("calls onClose when Back to Home is clicked", async () => {
    render(<SearchModeSelector />);
    await userEvent.click(screen.getByRole("button", { name: /back to home/i }));
    expect(mockWizard.onClose).toHaveBeenCalledOnce();
  });

  it("disables buttons when isBusy is true", () => {
    mockWizard.isBusy = true;
    render(<SearchModeSelector />);
    expect(screen.getByRole("button", { name: /use form/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /use ai chat/i })).toBeDisabled();
  });

  it("shows an error message when errorMessage is set", () => {
    mockWizard.errorMessage = "Something went wrong.";
    render(<SearchModeSelector />);
    expect(screen.getByText("Something went wrong.")).toBeInTheDocument();
  });

  it("shows 'Loading form...' while form is starting", async () => {
    mockWizard.startGuidedForm = vi.fn(() => new Promise(() => {}));
    render(<SearchModeSelector />);
    await userEvent.click(screen.getByRole("button", { name: /use form/i }));
    expect(screen.getByRole("button", { name: /loading form/i })).toBeInTheDocument();
  });

  it("shows 'Loading chat...' while chat is starting", async () => {
    mockWizard.startSmartChat = vi.fn(() => new Promise(() => {}));
    render(<SearchModeSelector />);
    await userEvent.click(screen.getByRole("button", { name: /use ai chat/i }));
    expect(screen.getByRole("button", { name: /loading chat/i })).toBeInTheDocument();
  });
});
