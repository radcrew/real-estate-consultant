"use client";

import { SearchWizardProvider } from "../../../contexts/search-wizard";
import { SearchModeSelector } from "./modes/selector";

import { STYLES } from "./styles";

type SearchWizardProps = {
  onClose: () => void;
};

export const SearchWizard = ({ onClose }: SearchWizardProps) => {
  return (
    <div className={STYLES.overlay}>
      <div className={STYLES.panel}>
        <div className={STYLES.content}>
          <SearchWizardProvider onClose={onClose}>
            <SearchModeSelector />
          </SearchWizardProvider>
        </div>
      </div>
    </div>
  );
};
