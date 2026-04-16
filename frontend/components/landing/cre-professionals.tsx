import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  ListChecks,
  Mail,
  Search,
  Shield,
  Zap,
} from "lucide-react";

import type { CreProfessionalFeatureId } from "@/constants";
import { CRE_PROFESSIONAL_FEATURES } from "@/constants";

const SECTION =
  "border-b border-border/60 bg-muted/30 px-4 py-14 sm:py-16";

const INNER = "mx-auto max-w-screen-xl";

const TITLE =
  "text-center text-2xl font-bold tracking-tight text-foreground sm:text-3xl";

const GRID =
  "mt-10 grid grid-cols-1 gap-6 md:grid-cols-2 md:gap-7 lg:grid-cols-3 lg:gap-8";

const CARD =
  "rounded-lg border border-border bg-card p-5 shadow-sm sm:p-6";

const ICON_WRAP =
  "mb-4 inline-flex rounded-lg bg-primary/15 p-3 text-primary";

const CARD_TITLE = "text-lg font-bold text-foreground";

const CARD_BODY =
  "mt-2 text-sm leading-relaxed text-muted-foreground sm:text-base";

const ICON_MAP: Record<CreProfessionalFeatureId, LucideIcon> = {
  "ai-fit-scoring": Zap,
  "saved-search-profiles": Search,
  "shortlist-status": ListChecks,
  "ai-outreach-drafts": Mail,
  "market-intelligence": BarChart3,
  "clear-height-transparency": Shield,
};

export const CreProfessionals = () => (
  <section
    className={SECTION}
    aria-labelledby="cre-professionals-heading"
  >
    <div className={INNER}>
      <h2 id="cre-professionals-heading" className={TITLE}>
        Built for CRE Professionals
      </h2>
      <div className={GRID}>
        {CRE_PROFESSIONAL_FEATURES.map((feature) => {
          const Icon = ICON_MAP[feature.id];
          return (
            <article key={feature.id} className={CARD}>
              <div className={ICON_WRAP}>
                <Icon className="size-6 shrink-0" aria-hidden />
              </div>
              <h3 className={CARD_TITLE}>{feature.title}</h3>
              <p className={CARD_BODY}>{feature.description}</p>
            </article>
          );
        })}
      </div>
    </div>
  </section>
)
