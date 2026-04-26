"use client";

import { SearchWizardProvider } from "../../contexts/search-wizard";
import { SearchModeSelector } from "./modes/search-mode-selector";

import { styles } from "./styles";

type SearchWizardProps = {
  onClose: () => void;
};

export const SearchWizard = ({ onClose }: SearchWizardProps) => {
  return (
    <div className={styles.overlay}>
      <div className={styles.panel}>
        <div className={styles.content}>
          <SearchWizardProvider onClose={onClose}>
            <SearchModeSelector />
          </SearchWizardProvider>
        </div>
      </div>
    </div>
  );
};
