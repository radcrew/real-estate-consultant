import { MapPinned, SlidersHorizontal, Warehouse } from "lucide-react";

import type { WizardQuestion } from "../types";

type QuestionInputShellProps = {
  question: WizardQuestion;
  stepIndex: number;
  totalSteps: number;
  children: React.ReactNode;
};

const QuestionIcon = ({ question }: { question: WizardQuestion }) => {
  if (question.id === "market") {
    return <MapPinned className="size-5" aria-hidden />;
  }

  if (question.id === "propertyTypes") {
    return <Warehouse className="size-5" aria-hidden />;
  }

  return <SlidersHorizontal className="size-5" aria-hidden />;
};

export const QuestionInputShell = ({
  question,
  stepIndex,
  totalSteps,
  children,
}: QuestionInputShellProps) => (
  <div className="space-y-5">
    <div className="flex items-center gap-3 text-xs text-muted-foreground sm:text-sm">
      <span className="inline-flex size-9 items-center justify-center rounded-full bg-primary/18 text-primary">
        <QuestionIcon question={question} />
      </span>
      <div>
        <p className="font-medium text-foreground">
          Step {stepIndex + 1} of {totalSteps}
        </p>
      </div>
    </div>

    <div className="space-y-3">
      <h3 className="text-2xl font-semibold tracking-tight sm:text-4xl">
        {question.title}
      </h3>

      {children}
    </div>
  </div>
);
