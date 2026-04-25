type ProgressBarProps = {
  stepIndex: number;
  totalSteps: number;
};

export const ProgressBar = ({ stepIndex, totalSteps }: ProgressBarProps) => {
  const safeTotalSteps = Math.max(totalSteps, 1);
  const currentStep = Math.min(stepIndex + 1, safeTotalSteps);
  const progressPercent =
    safeTotalSteps > 0 ? (currentStep / safeTotalSteps) * 100 : 0;
  const displayPercent = Math.round(progressPercent);

  return (
    <div className="w-full shrink-0">
      <div className="mb-2 flex items-baseline justify-between gap-3 text-xs text-muted-foreground sm:text-sm">
        <span className="font-medium tabular-nums text-foreground">
          Step {currentStep} of {safeTotalSteps}
        </span>
        <span className="tabular-nums">{displayPercent}% complete</span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-border/70"
        role="progressbar"
        aria-valuenow={displayPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Step ${currentStep} of ${safeTotalSteps}, ${displayPercent}% complete`}
      >
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-300 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
};
