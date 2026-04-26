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

import { styles } from "./styles";

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
    className={styles.section}
    aria-labelledby="cre-professionals-heading"
  >
    <div className={styles.inner}>
      <h2 id="cre-professionals-heading" className={styles.title}>
        Built for CRE Professionals
      </h2>
      <div className={styles.grid}>
        {CRE_PROFESSIONAL_FEATURES.map((feature) => {
          const Icon = ICON_MAP[feature.id];
          return (
            <article key={feature.id} className={styles.card}>
              <div className={styles.iconWrap}>
                <Icon className="size-6 shrink-0" aria-hidden />
              </div>
              <h3 className={styles.cardTitle}>{feature.title}</h3>
              <p className={styles.cardBody}>{feature.description}</p>
            </article>
          );
        })}
      </div>
    </div>
  </section>
);
