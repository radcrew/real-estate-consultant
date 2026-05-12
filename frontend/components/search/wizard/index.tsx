"use client";

import {
  SearchWizardProvider,
  useSearchWizard,
} from "@contexts/search-wizard";
import { GuidedQuestionnaire } from "./modes/guided";
import { SmartChat } from "./modes/llm";
import { SearchModeSelector } from "./modes/selector";

import { STYLES } from "./styles";

type SearchWizardProps = {
  sessionId?: string | null;
  onClose: () => void;
};

export const SearchWizard = ({ sessionId, onClose }: SearchWizardProps) => {
  return (
    <div className={STYLES.overlay}>
      <div className={STYLES.panel}>
        <div className={STYLES.content}>
          <SearchWizardProvider initialSessionId={sessionId} onClose={onClose}>
            <SearchWizardContent />
          </SearchWizardProvider>
        </div>
      </div>
    </div>
  );
};

const SearchWizardContent = () => {
  const { activeMode } = useSearchWizard();

  if (activeMode === "guided") {
    return <GuidedQuestionnaire />;
  }

  if (activeMode === "llm") {
    return <SmartChat />;
  }

  return <SearchModeSelector />;
};
