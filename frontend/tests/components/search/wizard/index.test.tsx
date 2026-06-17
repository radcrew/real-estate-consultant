// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SearchWizard } from "@components/search/wizard";

const mockActiveMode = { value: null as string | null };

vi.mock("@contexts/search-wizard", () => ({
  SearchWizardProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useSearchWizard: () => ({ activeMode: mockActiveMode.value }),
}));
vi.mock("@components/search/wizard/modes/selector", () => ({
  SearchModeSelector: () => <div data-testid="mode-selector" />,
}));
vi.mock("@components/search/wizard/modes/guided", () => ({
  GuidedQuestionnaire: () => <div data-testid="guided" />,
}));
vi.mock("@components/search/wizard/modes/llm", () => ({
  SmartChat: () => <div data-testid="smart-chat" />,
}));

describe("SearchWizard", () => {
  it("renders mode selector when activeMode is null", () => {
    mockActiveMode.value = null;
    render(<SearchWizard onClose={vi.fn()} />);
    expect(screen.getByTestId("mode-selector")).toBeInTheDocument();
  });

  it("renders GuidedQuestionnaire when activeMode is guided", () => {
    mockActiveMode.value = "guided";
    render(<SearchWizard onClose={vi.fn()} />);
    expect(screen.getByTestId("guided")).toBeInTheDocument();
  });

  it("renders SmartChat when activeMode is llm", () => {
    mockActiveMode.value = "llm";
    render(<SearchWizard onClose={vi.fn()} />);
    expect(screen.getByTestId("smart-chat")).toBeInTheDocument();
  });
});
