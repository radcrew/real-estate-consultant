"use client";

import { ChevronLeft, Sparkles } from "lucide-react";

import { Button } from "@components/ui/button";

import { useSearchWizard } from "@contexts/search-wizard";

import { styles } from "./styles";

export const SmartChat = () => {
  const { resetToChooser } = useSearchWizard();

  return (
    <div className={styles.wrapper}>
      <section className={styles.panel}>
        <div className="flex size-12 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
          <Sparkles className="size-6" aria-hidden />
        </div>

        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-600">
            Smart Chat
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
            AI chat flow is the next step
          </h2>
          <p className="mt-3 text-base leading-7 text-slate-500">
            The new selection architecture is ready. We can plug the actual
            conversational search experience into this branch next.
          </p>
        </div>

        <div className="mt-8 flex justify-start border-t border-border/70 pt-6">
          <Button
            variant="outline"
            className="h-9 px-3 text-sm"
            onClick={resetToChooser}
          >
            <ChevronLeft className="size-4" aria-hidden />
            Back
          </Button>
        </div>
      </section>
    </div>
  );
};
