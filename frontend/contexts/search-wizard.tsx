"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren,
} from "react";
import { useRouter } from "next/navigation";

import { useIntakeSessions } from "@hooks/use-intake-sessions";
import { getApiErrorMessage } from "@utils/common";

import type {
  AnswerValue,
  SummaryRow,
  WizardAnswers,
  WizardQuestion,
} from "../components/search/wizard/types";
import {
  formatAnswerForSummary,
  getDefaultAnswer,
  isQuestionComplete,
  parseQuestion,
} from "../components/search/wizard/utils";

export type SearchWizardMode = "selector" | "guided" | "llm";

type SearchWizardContextValue = {
  activeMode: SearchWizardMode;
  canContinue: boolean;
  currentAnswer: AnswerValue | undefined;
  currentQuestion: WizardQuestion | null;
  errorMessage: string | null;
  goNext: () => Promise<void>;
  isBusy: boolean;
  isLoadingQuestion: boolean;
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
  llmChatBootstrap: string[] | null;
  clearLlmChatBootstrap: () => void;
};

const SearchWizardContext = createContext<SearchWizardContextValue | null>(null);

type SearchWizardProviderProps = PropsWithChildren<{
  initialSessionId?: string | null;
  onClose: () => void;
}>;

export const SearchWizardProvider = ({
  children,
  initialSessionId,
  onClose,
}: SearchWizardProviderProps) => {
  const router = useRouter();
  const { createSession, getSession, submitAnswer, completeSession } =
    useIntakeSessions();
  const [activeMode, setActiveMode] = useState<SearchWizardMode>(() =>
    initialSessionId ? "guided" : "selector",
  );
  const [stepIndex, setStepIndex] = useState(0);
  const [totalSteps, setTotalSteps] = useState<number>(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<WizardQuestion | null>(
    null,
  );
  const [questionHistory, setQuestionHistory] = useState<WizardQuestion[]>([]);
  const [summaryRows, setSummaryRows] = useState<SummaryRow[]>([]);
  const [answers, setAnswers] = useState<WizardAnswers>({});
  const [isLoadingQuestion, setLoadingQuestion] = useState(() =>
    Boolean(initialSessionId),
  );
  const [isSubmitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [llmChatBootstrap, setLlmChatBootstrap] = useState<string[] | null>(
    null,
  );

  const currentAnswer = currentQuestion ? answers[currentQuestion.id] : undefined;
  const canContinue =
    currentQuestion != null && isQuestionComplete(currentQuestion, currentAnswer);
  const isBusy = isLoadingQuestion || isSubmitting;

  useEffect(() => {
    if (!initialSessionId) {
      return;
    }

    let isCancelled = false;

    const hydrateSession = async () => {
      setActiveMode("guided");
      setLoadingQuestion(true);
      setSubmitting(false);
      setErrorMessage(null);

      try {
        const response = await getSession(initialSessionId);

        if (isCancelled) {
          return;
        }

        const criteria = response.criteria ?? {};
        const answeredQuestions = response.question_history?.map(parseQuestion) ?? [];
        const nextQuestion = response.next_question ? parseQuestion(response.next_question) : null;
        const visibleHistory = nextQuestion ? [...answeredQuestions, nextQuestion] : answeredQuestions;
        const currentQuestionToShow =
          nextQuestion ??
          answeredQuestions[answeredQuestions.length - 1] ??
          null;
        const summaryQuestions = nextQuestion ? answeredQuestions : answeredQuestions.slice(0, -1);
        const hydratedAnswers = Object.fromEntries(
          visibleHistory.map((question) => [
            question.id,
            criteria[question.id] ?? getDefaultAnswer(question),
          ]),
        );
        const total = response.total_questions ?? 1;
        const hydratedStepIndex = response.current_index ?? answeredQuestions.length;

        setSessionId(response.id ?? initialSessionId);
        setTotalSteps(total);
        setCurrentQuestion(currentQuestionToShow);
        setQuestionHistory(visibleHistory);
        setAnswers(hydratedAnswers);
        setSummaryRows(
          summaryQuestions.map((question) => ({
            id: question.id,
            label: question.title,
            value: formatAnswerForSummary(question, criteria[question.id]),
          })),
        );
        setStepIndex(hydratedStepIndex);
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(getApiErrorMessage(error));
          setCurrentQuestion(null);
        }
      } finally {
        if (!isCancelled) {
          setLoadingQuestion(false);
        }
      }
    };

    hydrateSession();

    return () => {
      isCancelled = true;
    };
  }, [getSession, initialSessionId]);

  const startGuidedForm = async () => {
    if (isLoadingQuestion || isSubmitting) {
      return;
    }

    setLoadingQuestion(true);
    setErrorMessage(null);

    try {
      const response = await createSession("guided");
      if (!response.first_question) {
        setErrorMessage(
          "The server is temporarily unavailable. Please try again later.",
        );
        setActiveMode("selector");
        return;
      }

      setSessionId(response.session_id);
      router.push(`/questionnaire/${response.session_id}`);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
      setActiveMode("selector");
    } finally {
      setLoadingQuestion(false);
    }
  };

  const startSmartChat = async () => {
    if (isLoadingQuestion || isSubmitting) {
      return;
    }

    setLoadingQuestion(true);
    setErrorMessage(null);

    try {
      const response = await createSession("llm");
      setSessionId(response.session_id);
      const parts: string[] = [];
      const welcome = response.message?.trim();
      if (welcome) {
        parts.push(welcome);
      }
      const followUp = response.next_question?.text?.trim();
      if (followUp) {
        parts.push(followUp);
      }
      setLlmChatBootstrap(parts.length > 0 ? parts : null);
      setActiveMode("llm");
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
      setActiveMode("selector");
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

      const response = await submitAnswer(sessionId, {
        key: currentQuestion.id,
        answers: answerToSubmit,
      });

      const newSummaryRow = {
        id: currentQuestion.id,
        label: currentQuestion.title,
        value: formatAnswerForSummary(currentQuestion, answerToSubmit),
      };

      setSummaryRows((current) => [...current, newSummaryRow]);

      if (response.next_question == null) {
        const completed = await completeSession(sessionId);
        const profileId = completed.search_profile_id;
        if (!profileId) {
          setErrorMessage("Search profile was not created. Please try again.");
          return;
        }
        
        setStepIndex(totalSteps);
        await new Promise((resolve) => setTimeout(resolve, 550));
        onClose();
        router.push(`/search/${profileId}`);
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
        [nextQuestion.id]:
          current[nextQuestion.id] ?? getDefaultAnswer(nextQuestion),
      }));
      setStepIndex((current) => current + 1);
    } catch (error) {
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setSubmitting(false);
    }
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
    setLlmChatBootstrap(null);
  };

  const resetToChooser = () => {
    resetQuestionnaireState();
    setActiveMode("selector");
  };

  
  const clearLlmChatBootstrap = useCallback(() => {
    setLlmChatBootstrap(null);
  }, []);

  const value: SearchWizardContextValue = {
    activeMode,
    canContinue,
    currentAnswer,
    currentQuestion,
    errorMessage,
    goNext,
    isBusy,
    isLoadingQuestion,
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
    llmChatBootstrap,
    clearLlmChatBootstrap,
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
