"use client";

import { SearchWizardProvider } from "../../contexts/search-wizard";
import { SearchModeSelector } from "./modes/search-mode-selector";

type SearchWizardProps = {
  onClose: () => void;
};

const OVERLAY_CLASS_NAME = [
  "fixed inset-0 z-50 flex min-h-screen",
  "bg-slate-950/70 backdrop-blur-sm",
].join(" ");

const PANEL_CLASS_NAME = [
  "flex min-h-screen w-full flex-col overflow-hidden",
  "bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.18),_transparent_28%),linear-gradient(180deg,_rgba(255,255,255,0.98),_rgba(248,250,252,0.98))]",
  "text-foreground",
].join(" ");

const CONTENT_CLASS_NAME = [
  "mx-auto flex w-full max-w-5xl flex-1 flex-col",
  "px-4 pt-5 pb-6 sm:px-6 lg:px-8",
].join(" ");

export const SearchWizard = ({ onClose }: SearchWizardProps) => {
  return (
    <div className={OVERLAY_CLASS_NAME}>
      <div className={PANEL_CLASS_NAME}>
        <div className={CONTENT_CLASS_NAME}>
          <SearchWizardProvider onClose={onClose}>
            <SearchModeSelector />
          </SearchWizardProvider>
        </div>
      </div>
    </div>
  );
};
