/**
 * Centralized RadEstate brand + copy, mirroring Voyager's `config/brand.ts`.
 *
 * Voyager-style sections (hero, featured grid, account workspace, etc.) read
 * their text from here instead of hardcoding it, so product copy lives in one
 * place. Consumed by the page compositions built in Phase B onward.
 */
export const brand = {
  name: "RadEstate",
  tagline: "AI-assisted commercial real estate search",

  hero: {
    title: "Find your next commercial property with AI",
    subtitle:
      "Professional-grade CRE platform with AI-powered fit scoring, broker-style search, and outreach draft generation.",
    primaryCta: { label: "Start Searching", href: "/questionnaire" },
    secondaryCta: { label: "Sign In", href: "/sign-in" },
  },

  sections: {
    featured: {
      heading: "Featured listings",
      subHeading: "Curated commercial properties across categories and markets.",
    },
    listings: {
      heading: "Browse properties",
      subHeading: "Search and filter commercial listings.",
    },
  },

  account: {
    workspaceLabel: "Member workspace",
    title: "Your account",
    subtitle: "Manage your profile, saved searches, and security.",
  },
} as const;

export type Brand = typeof brand;
