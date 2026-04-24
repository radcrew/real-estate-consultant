import { WIZARD_QUESTIONS } from "./questions";

type ProgressBarProps = {
  stepIndex: number;
}

export const ProgressBar = ({ stepIndex }: ProgressBarProps) => {
  const progressValue = ((stepIndex + 1) / WIZARD_QUESTIONS.length) * 100;

  return (
    <div className="absolute inset-x-0 top-0 h-1 bg-border/60">
      <div
      className="h-full bg-primary transition-[width] duration-300 ease-out"
      style={{ width: `${progressValue}%` }}
      />
    </div>
  );
}