import { HERO_STATS } from "@constants";

import { HeroActions } from "./hero-actions";

import { styles } from "./styles";

export const Hero = () => (
  <section className={styles.section}>
    <div className={styles.inner}>
      <div className={styles.headlineStack}>
        <span className={styles.headlineStrip}>Find Your Next Commercial</span>
        <span className={styles.headlineStrip}>Property with AI</span>
      </div>

      <p className={styles.subcopy}>
        Professional-grade CRE platform with AI-powered fit scoring, broker-style
        search, and outreach draft generation.
      </p>

      <HeroActions />
    </div>
    <div className={styles.statsSection}>
      <div className={styles.statsGrid}>
        {HERO_STATS.map(({ label, value }) => (
          <div key={label} className={styles.statCell}>
            <p className={styles.statValue}>{value}</p>
            <p className={styles.statLabel}>{label}</p>
          </div>
        ))}
      </div>
    </div>
  </section>
);
