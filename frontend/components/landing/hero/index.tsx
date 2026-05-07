import { HERO_STATS } from "@constants";

import { HeroActions } from "./actions";

import { STYLES } from "./styles";

export const Hero = () => (
  <section className={STYLES.section}>
    <div className={STYLES.inner}>
      <div className={STYLES.headlineStack}>
        <span className={STYLES.headlineStrip}>Find Your Next Commercial</span>
        <span className={STYLES.headlineStrip}>Property with AI</span>
      </div>

      <p className={STYLES.subcopy}>
        Professional-grade CRE platform with AI-powered fit scoring, broker-style
        search, and outreach draft generation.
      </p>

      <HeroActions />
    </div>
    <div className={STYLES.statsSection}>
      <div className={STYLES.statsGrid}>
        {HERO_STATS.map(({ label, value }) => (
          <div key={label} className={STYLES.statCell}>
            <p className={STYLES.statValue}>{value}</p>
            <p className={STYLES.statLabel}>{label}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);
