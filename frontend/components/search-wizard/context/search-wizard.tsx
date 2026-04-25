"use client";

import {
  createContext,
  useContext,
  type PropsWithChildren,
} from "react";

import {
  useSearchWizardFlow,
  type SearchMode,
} from "../use-search-wizard-flow";
import type { AnswerValue, WizardQuestion } from "../types";

type SearchWizardContextValue = {
  canContinue: boolean;
  currentAnswer: AnswerValue | undefined;
  currentQuestion: WizardQuestion | null;
  errorMessage: string | null;
  goToNextQuestion: () => Promise<void>;
  isBusy: boolean;
  isLoadingQuestion: boolean;
  isSubmitting: boolean;
  mode: SearchMode;
  onClose: () => void;
  resetToChooser: () => void;
  setErrorMessage: (value: string | null) => void;
  showSmartChat: () => void;
  startGuidedForm: () => Promise<void>;
  stepIndex: number;
  updateCurrentAnswer: (value: AnswerValue) => void;
  toggleCurrentMultiSelect: (value: string) => void;
};

const SearchWizardContext = createContext<SearchWizardContextValue | null>(null);

type SearchWizardProviderProps = PropsWithChildren<{
  onClose: () => void;
}>;

export const SearchWizardProvider = ({
  children,
  onClose,
}: SearchWizardProviderProps) => {
  const value = useSearchWizardFlow({ onClose });

  return (
    <SearchWizardContext.Provider value={{ ...value, onClose }}>
      {children}
    </SearchWizardContext.Provider>
  );
};

export const useSearchWizard = () => {
  const context = useContext(SearchWizardContext);

  if (!context) {
    throw new Error("useSearchWizard must be used within SearchWizardProvider");
  }

  return context;
};
