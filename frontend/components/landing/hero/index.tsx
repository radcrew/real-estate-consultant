import Image from "next/image";

import { HERO_STATS } from "@constants";

import { HeroActions } from "./actions";

import { STYLES } from "./styles";

export const Hero = () => (
  <section className={STYLES.section}>
    <div className={STYLES.inner}>
      <div className={STYLES.left}>
        <h1 className={STYLES.headline}>
          Find your next commercial property with AI
        </h1>
        <p className={STYLES.subcopy}>
          Professional-grade CRE platform with AI-powered fit scoring,
          broker-style search, and outreach draft generation.
        </p>
        <HeroActions />
      </div>

      <div className={STYLES.imageWrap}>
        <Image
          src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1200&q=80"
          alt="Modern commercial building"
          fill
          priority
          sizes="(max-width: 1024px) 100vw, 50vw"
          className="object-cover"
        />
      </div>
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
