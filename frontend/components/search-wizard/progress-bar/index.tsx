import { styles } from "./styles";

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
    <div className={styles.root}>
      <div className={styles.header}>
        <span className={styles.stepLabel}>
          Step {currentStep} of {safeTotalSteps}
        </span>
        <span className={styles.percentLabel}>{displayPercent}% complete</span>
      </div>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={displayPercent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`Step ${currentStep} of ${safeTotalSteps}, ${displayPercent}% complete`}
      >
        <div
          className={styles.fill}
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
};
