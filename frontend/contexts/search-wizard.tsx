"use client";

import {
  createContext,
  useContext,
  useState,
  type PropsWithChildren,
} from "react";
import { useRouter } from "next/navigation";

import { getApiErrorMessage } from "@lib/api-errors";
import {
  intakeSessionsService,
} from "@services/intake-sessions";

import type {
  AnswerValue,
  SummaryRow,
  WizardAnswers,
  WizardQuestion,
} from "../components/search-wizard/types";
import {
  formatAnswerForSummary,
  getDefaultAnswer,
  isQuestionComplete,
  parseQuestion,
} from "../components/search-wizard/utils";

type SearchWizardContextValue = {
  canContinue: boolean;
  currentAnswer: AnswerValue | undefined;
  currentQuestion: WizardQuestion | null;
  errorMessage: string | null;
  goNext: () => Promise<void>;
  isBusy: boolean;
  isGuidedFormOpen: boolean;
  isLoadingQuestion: boolean;
  isSmartChatOpen: boolean;
  isSubmitting: boolean;
  onClose: () => void;
  goPrev: () => void;
  resetToChooser: () => void;
  setErrorMessage: (value: string | null) => void;
  startGuidedForm: () => Promise<void>;
  startSmartChat: () => Promise<void>;
  stepIndex: number;
  summaryRows: SummaryRow[];
  totalSteps: number;
  updateCurrentAnswer: (value: AnswerValue) => void;
  toggleCurrentMultiSelect: (value: string) => void;
  sessionId: string | null;
};

const SearchWizardContext = createContext<SearchWizardContextValue | null>(null);

type SearchWizardProviderProps = PropsWithChildren<{
  onClose: () => void;
}>;

export const SearchWizardProvider = ({
  children,
  onClose,
}: SearchWizardProviderProps) => {
  const router = useRouter();
  const [isGuidedFormOpen, setGuidedFormOpen] = useState(false);
  const [isSmartChatOpen, setSmartChatOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [totalSteps, setTotalSteps] = useState(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<WizardQuestion | null>(
    null,
  );
  const [questionHistory, setQuestionHistory] = useState<WizardQuestion[]>([]);
  const [summaryRows, setSummaryRows] = useState<SummaryRow[]>([]);
  const [answers, setAnswers] = useState<WizardAnswers>({});
  const [isLoadingQuestion, setLoadingQuestion] = useState(false);
  const [isSubmitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;
  const canContinue = currentQuestion != null && isQuestionComplete(currentQuestion, currentAnswer);
  const isBusy = isLoadingQuestion || isSubmitting;

  const resetQuestionnaireState = () => {
    setSessionId(null);
    setCurrentQuestion(null);
    setQuestionHistory([]);
    setSummaryRows([]);
    setAnswers({});
    setStepIndex(0);
    setTotalSteps(1);
    setLoadingQuestion(false);
    setSubmitting(false);
    setErrorMessage(null);
  };

  const resetToChooser = () => {
    resetQuestionnaireState();
    setGuidedFormOpen(false);
    setSmartChatOpen(false);
  };

  const startGuidedForm = async () => {
    if (isLoadingQuestion || isSubmitting) {
      return;
    }

    setGuidedFormOpen(true);
    setSmartChatOpen(false);
    setLoadingQuestion(true);
    setErrorMessage(null);

    try {
      const response = await intakeSessionsService.createSession();
      const firstQuestion = parseQuestion(response.first_question);

      setSessionId(response.session_id);
      setTotalSteps(Math.max(response.total_questions ?? 1, 1));
      setCurrentQuestion(firstQuestion);
      setQuestionHistory([firstQuestion]);
      setAnswers({
        [firstQuestion.id]: getDefaultAnswer(firstQuestion),
      });
      setStepIndex(0);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
      setGuidedFormOpen(false);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const startSmartChat = async () => {
    if (isLoadingQuestion || isSubmitting) {
      return;
    }

    setGuidedFormOpen(false);
    setSmartChatOpen(true);
    setLoadingQuestion(true);
    setErrorMessage(null);

    try {
      const response = await intakeSessionsService.createSession();
      setSessionId(response.session_id);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
      setSmartChatOpen(false);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const goPrev = () => {
    if (isLoadingQuestion || isSubmitting) {
      return;
    }

    if (stepIndex <= 0) {
      resetToChooser();
      return;
    }

    const previousIndex = stepIndex - 1;
    const previousQuestion = questionHistory[previousIndex];

    if (!previousQuestion) {
      resetToChooser();
      return;
    }

    setCurrentQuestion(previousQuestion);
    setStepIndex(previousIndex);
    setSummaryRows((current) => current.slice(0, -1));
  };

  const updateCurrentAnswer = (value: AnswerValue) => {
    if (!currentQuestion) {
      return;
    }

    setAnswers((current) => ({
      ...current,
      [currentQuestion.id]: value,
    }));
  };

  const toggleCurrentMultiSelect = (value: string) => {
    if (!currentQuestion) {
      return;
    }

    const current = answers[currentQuestion.id];
    const selected = Array.isArray(current) ? current : [];

    setAnswers((existing) => ({
      ...existing,
      [currentQuestion.id]: selected.includes(value)
        ? selected.filter((item) => item !== value)
        : [...selected, value],
    }));
  };

  const goNext = async () => {
    if (
      !currentQuestion ||
      !sessionId ||
      !canContinue ||
      isLoadingQuestion ||
      isSubmitting
    ) {
      return;
    }

    setSubmitting(true);
    setErrorMessage(null);

    try {
      const answerToSubmit = answers[currentQuestion.id];

      if (answerToSubmit === undefined) {
        return;
      }

      const response = await intakeSessionsService.submitAnswer(sessionId, {
        key: currentQuestion.id,
        answers: answerToSubmit,
      });

      setSummaryRows((current) => [
        ...current,
        {
          id: currentQuestion.id,
          label: currentQuestion.title,
          value: formatAnswerForSummary(currentQuestion, answerToSubmit),
        },
      ]);

      if (response.next_question == null) {
        await intakeSessionsService.completeSession(sessionId);
        setStepIndex(totalSteps);
        await new Promise((resolve) => setTimeout(resolve, 550));
        onClose();
        router.push("/");
        return;
      }

      const nextQuestion = parseQuestion(response.next_question);

      setCurrentQuestion(nextQuestion);
      setQuestionHistory((current) => [
        ...current.slice(0, stepIndex + 1),
        nextQuestion,
      ]);
      setAnswers((current) => ({
        ...current,
        [nextQuestion.id]: current[nextQuestion.id] ?? getDefaultAnswer(nextQuestion),
      }));
      setStepIndex((current) => current + 1);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  const value: SearchWizardContextValue = {
    canContinue,
    currentAnswer,
    currentQuestion,
    errorMessage,
    goNext,
    isBusy,
    isGuidedFormOpen,
    isLoadingQuestion,
    isSmartChatOpen,
    isSubmitting,
    onClose,
    goPrev,
    resetToChooser,
    setErrorMessage,
    startGuidedForm,
    startSmartChat,
    stepIndex,
    summaryRows,
    totalSteps,
    updateCurrentAnswer,
    toggleCurrentMultiSelect,
    sessionId,
  };

  return (
    <SearchWizardContext.Provider value={value}>
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
