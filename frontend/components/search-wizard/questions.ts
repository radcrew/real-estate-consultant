import type { WizardQuestion } from "./types";

export const WIZARD_QUESTIONS: WizardQuestion[] = [
  {
    id: "market",
    kind: "text",
    title: "Where are you looking?",
    description:
      "Tell us the market, city, state, or submarket you want to prioritize first.",
    placeholder: "Dallas-Fort Worth, TX",
    required: true,
  },
  {
    id: "listingType",
    kind: "single-select",
    title: "Is this a sale or lease search?",
    description:
      "We'll use this to frame the rest of the criteria and ranking logic.",
    required: true,
    options: [
      { label: "For lease", value: "lease", hint: "Tenant requirement" },
      { label: "For sale", value: "sale", hint: "Acquisition requirement" },
      {
        label: "Open to both",
        value: "both",
        hint: "Show opportunities across both tracks",
      },
    ],
  },
  {
    id: "propertyTypes",
    kind: "multi-select",
    title: "What property types fit this search?",
    description:
      "Pick all that apply. Later we can ask follow-up questions based on the mix.",
    required: true,
    options: [
      { label: "Industrial", value: "industrial", hint: "Warehouse and logistics" },
      { label: "Flex", value: "flex", hint: "Light industrial and office mix" },
      { label: "Retail", value: "retail", hint: "Storefront and shopping center" },
    ],
  },
  {
    id: "minSize",
    kind: "range",
    title: "What is the minimum size target?",
    description:
      "Start with the floor requirement. We can expand this into min/max ranges next.",
    min: 5000,
    max: 150000,
    step: 5000,
    unit: "SF",
    minLabel: "5k SF",
    maxLabel: "150k SF",
    required: true,
  },
  {
    id: "budget",
    kind: "range",
    title: "What budget should we anchor around?",
    description:
      "Use this as a starting point for ranking. Hard caps and deal-breakers can come next.",
    min: 1000000,
    max: 20000000,
    step: 250000,
    unit: "$",
    minLabel: "$1M",
    maxLabel: "$20M",
    required: true,
  },
];
