// @vitest-environment jsdom
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { GuidedQuestionnaire } from "@components/search/wizard/modes/guided";
import type { TextQuestion } from "@components/search/wizard/types";

const TEXT_QUESTION: TextQuestion = {
  id: "neighborhood",
  kind: "text",
  title: "Preferred neighborhood?",
  description: "Enter the area you prefer.",
};

const mockWizard = {
  canContinue: true,
  currentAnswer: "" as string,
  currentQuestion: TEXT_QUESTION as TextQuestion | null,
  errorMessage: null as string | null,
  goNext: vi.fn(),
  goPrev: vi.fn(),
  isBusy: false,
  isLoadingQuestion: false,
  isSubmitting: false,
  summaryRows: [] as { id: string; label: string; value: string }[],
  stepIndex: 0,
  totalSteps: 5,
  toggleCurrentMultiSelect: vi.fn(),
  updateCurrentAnswer: vi.fn(),
};

vi.mock("@contexts/search-wizard", () => ({
  useSearchWizard: () => mockWizard,
}));

beforeEach(() => {
  mockWizard.canContinue = true;
  mockWizard.currentQuestion = TEXT_QUESTION;
  mockWizard.errorMessage = null;
  mockWizard.isBusy = false;
  mockWizard.isSubmitting = false;
  mockWizard.stepIndex = 0;
  mockWizard.totalSteps = 5;
  mockWizard.goNext = vi.fn();
  mockWizard.goPrev = vi.fn();
});

describe("GuidedQuestionnaire", () => {
  it("renders the progress bar", () => {
    render(<GuidedQuestionnaire />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("renders the current question title", () => {
    render(<GuidedQuestionnaire />);
    expect(screen.getByRole("heading", { name: /preferred neighborhood/i })).toBeInTheDocument();
  });

  it("renders Back and Continue buttons", () => {
    render(<GuidedQuestionnaire />);
    expect(screen.getByRole("button", { name: /back/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /continue/i })).toBeInTheDocument();
  });

  it("calls goNext when Continue is clicked", async () => {
    render(<GuidedQuestionnaire />);
    await userEvent.click(screen.getByRole("button", { name: /continue/i }));
    expect(mockWizard.goNext).toHaveBeenCalledOnce();
  });

  it("calls goPrev when Back is clicked", async () => {
    render(<GuidedQuestionnaire />);
    await userEvent.click(screen.getByRole("button", { name: /back/i }));
    expect(mockWizard.goPrev).toHaveBeenCalledOnce();
  });

  it("shows 'Search' on the last step", () => {
    mockWizard.stepIndex = 4;
    mockWizard.totalSteps = 5;
    render(<GuidedQuestionnaire />);
    expect(screen.getByRole("button", { name: /search/i })).toBeInTheDocument();
  });

  it("shows 'Searching...' while submitting on last step", () => {
    mockWizard.stepIndex = 4;
    mockWizard.totalSteps = 5;
    mockWizard.isSubmitting = true;
    render(<GuidedQuestionnaire />);
    expect(screen.getByRole("button", { name: /searching/i })).toBeInTheDocument();
  });

  it("disables Continue when canContinue is false", () => {
    mockWizard.canContinue = false;
    render(<GuidedQuestionnaire />);
    expect(screen.getByRole("button", { name: /continue/i })).toBeDisabled();
  });

  it("shows loading message when question is loading", () => {
    mockWizard.currentQuestion = null;
    mockWizard.isLoadingQuestion = true;
    render(<GuidedQuestionnaire />);
    expect(screen.getByText("Loading your questionnaire...")).toBeInTheDocument();
  });

  it("shows error message when errorMessage is set", () => {
    mockWizard.errorMessage = "Failed to load.";
    render(<GuidedQuestionnaire />);
    expect(screen.getByText("Failed to load.")).toBeInTheDocument();
  });

  it("shows summary panel", () => {
    render(<GuidedQuestionnaire />);
    expect(screen.getByText("Your Answers")).toBeInTheDocument();
  });
});
