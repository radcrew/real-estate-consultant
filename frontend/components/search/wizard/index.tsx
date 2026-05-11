"use client";

import { SearchWizardProvider } from "../../../contexts/search-wizard";
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
            <SearchModeSelector />
          </SearchWizardProvider>
        </div>
      </div>
    </div>
  );
};
