import { STYLES } from "./styles";

type ProgressBarProps = {
  stepIndex: number;
  totalSteps: number;
};

export const ProgressBar = ({ stepIndex, totalSteps }: ProgressBarProps) => {
  const safeTotalSteps = Math.max(totalSteps, 1);
  const currentStep = Math.min(stepIndex + 1, safeTotalSteps);
  const completedSteps = Math.min(Math.max(stepIndex, 0), safeTotalSteps);
  const progressPercent =
    safeTotalSteps > 0 ? (completedSteps / safeTotalSteps) * 100 : 0;
  const displayPercent = Math.round(progressPercent);

  return (
    <div className={STYLES.root}>
      <div className={STYLES.header}>
        <span className={STYLES.stepLabel}>
          Step {currentStep} of {safeTotalSteps}
        </span>
        <span className={STYLES.percentLabel}>{displayPercent}% complete</span>
      </div>
      <div
        className={STYLES.track}
        role="progressbar"
        aria-valuenow={displayPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Step ${currentStep} of ${safeTotalSteps}, ${displayPercent}% complete`}
      >
        <div
          className={STYLES.fill}
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
};
