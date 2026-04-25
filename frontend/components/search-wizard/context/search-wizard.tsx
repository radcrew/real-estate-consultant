"use client";

import {
  createContext,
  useContext,
  useState,
  type PropsWithChildren,
} from "react";
import { useRouter } from "next/navigation";

import { getApiErrorMessage } from "@lib/api-errors";
import { intakeSessionsService } from "@services/intake-sessions";

import { mapApiQuestionToWizardQuestion } from "../map-api-question";
import type { AnswerValue, WizardAnswers, WizardQuestion } from "../types";
import { getDefaultAnswer, isQuestionComplete } from "../utils";

type SearchWizardContextValue = {
  canContinue: boolean;
  currentAnswer: AnswerValue | undefined;
  currentQuestion: WizardQuestion | null;
  errorMessage: string | null;
  goToNextQuestion: () => Promise<void>;
  isBusy: boolean;
  isGuidedFormOpen: boolean;
  isLoadingQuestion: boolean;
  isSmartChatOpen: boolean;
  isSubmitting: boolean;
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
  const router = useRouter();
  const [isGuidedFormOpen, setGuidedFormOpen] = useState(false);
  const [isSmartChatOpen, setSmartChatOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<WizardQuestion | null>(
    null,
  );
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
    setAnswers({});
    setStepIndex(0);
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
      const firstQuestion = mapApiQuestionToWizardQuestion(
        response.first_question,
      );

      setSessionId(response.session_id);
      setCurrentQuestion(firstQuestion);
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

  const showSmartChat = () => {
    setErrorMessage(null);
    setSmartChatOpen(true);
    setGuidedFormOpen(false);
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

  const goToNextQuestion = async () => {
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

      if (response.next_question == null) {
        onClose();
        router.push("/");
        return;
      }

      const nextQuestion = mapApiQuestionToWizardQuestion(response.next_question);

      setCurrentQuestion(nextQuestion);
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
    goToNextQuestion,
    isBusy,
    isGuidedFormOpen,
    isLoadingQuestion,
    isSmartChatOpen,
    isSubmitting,
    onClose,
    resetToChooser,
    setErrorMessage,
    showSmartChat,
    startGuidedForm,
    stepIndex,
    updateCurrentAnswer,
    toggleCurrentMultiSelect,
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
