import type { LucideIcon } from "lucide-react";
import {
  BarChart3,
  ListChecks,
  Mail,
  Search,
  Shield,
  Zap,
} from "lucide-react";

import type { CreProfessionalFeatureId } from "@constants";
import { CRE_PROFESSIONAL_FEATURES } from "@constants";

import { STYLES } from "./styles";

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
    className={STYLES.section}
    aria-labelledby="cre-professionals-heading"
  >
    <div className={STYLES.inner}>
      <h2 id="cre-professionals-heading" className={STYLES.title}>
        Built for CRE Professionals
      </h2>
      <div className={STYLES.grid}>
        {CRE_PROFESSIONAL_FEATURES.map((feature) => {
          const Icon = ICON_MAP[feature.id];
          return (
            <article key={feature.id} className={STYLES.card}>
              <div className={STYLES.iconWrap}>
                <Icon className="size-6 shrink-0" aria-hidden />
              </div>
              <h3 className={STYLES.cardTitle}>{feature.title}</h3>
              <p className={STYLES.cardBody}>{feature.description}</p>
            </article>
          );
        })}
      </div>
    </div>
  </section>
);
