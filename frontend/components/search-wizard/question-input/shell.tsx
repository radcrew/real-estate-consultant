import type { WizardQuestion } from "../types";

type QuestionInputShellProps = {
  question: WizardQuestion;
  children: React.ReactNode;
};

export const QuestionInputShell = ({
  question,
  children,
}: QuestionInputShellProps) => (
  <div>
    <h3 className="text-lg font-semibold tracking-tight sm:text-xl">
      {question.title}
    </h3>

    <div className="mt-6 sm:mt-7">{children}</div>
  </div>
);
