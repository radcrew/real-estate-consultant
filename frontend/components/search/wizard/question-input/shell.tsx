import type { WizardQuestion } from "../types";
import { getQuestionInputDisplayTitle } from "../utils";

type QuestionInputShellProps = {
  question: WizardQuestion;
  children: React.ReactNode;
};

export const QuestionInputShell = ({
  question,
  children,
}: QuestionInputShellProps) => (
  <div>
    <h3 className="text-left text-lg font-semibold tracking-tight sm:text-xl">
      {getQuestionInputDisplayTitle(question)}
    </h3>
    <p className="mt-1 text-left text-sm text-muted-foreground sm:text-base">
      {question.description}
    </p>

    <div className="mt-6 sm:mt-7">{children}</div>
  </div>
);
