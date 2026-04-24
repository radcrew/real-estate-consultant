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
    return <MapPinned className="size-4" aria-hidden />;
  }

  if (question.id === "propertyTypes") {
    return <Warehouse className="size-4" aria-hidden />;
  }

  return <SlidersHorizontal className="size-4" aria-hidden />;
};

export const QuestionInputShell = ({
  question,
  stepIndex,
  totalSteps,
  children,
}: QuestionInputShellProps) => (
  <div className="space-y-4">
    <div className="flex items-center gap-2.5 text-xs text-muted-foreground">
      <span className="inline-flex size-8 items-center justify-center rounded-full bg-primary/18 text-primary">
        <QuestionIcon question={question} />
      </span>
      <div>
        <p className="font-medium text-foreground">
          Step {stepIndex + 1} of {totalSteps}
        </p>
      </div>
    </div>

    <div className="space-y-2.5">
      <h3 className="text-base font-semibold tracking-tight sm:text-lg">
        {question.title}
      </h3>

      {children}
    </div>
  </div>
);
