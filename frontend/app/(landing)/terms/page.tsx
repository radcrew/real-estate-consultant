import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "The terms for using RadEstate",
};

const SECTIONS = [
  {
    title: "Using RadEstate",
    body: "RadEstate provides AI-assisted commercial real estate search, fit scoring, and outreach drafting. You agree to use the platform for lawful, professional real estate purposes.",
  },
  {
    title: "Listings & accuracy",
    body: "Listing data and AI scores are provided for guidance and may be inferred or incomplete. Always verify specifications, pricing, and availability directly with the listing broker before acting.",
  },
  {
    title: "Outreach",
    body: "Outreach drafts are suggestions for your review. You are responsible for any communications you choose to send.",
  },
  {
    title: "Accounts",
    body: "You are responsible for keeping your account credentials secure and for activity under your account.",
  },
];

const TermsPage = () => (
  <div className="mx-auto max-w-3xl px-4 py-16 lg:py-24">
    <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
      Terms of Service
    </h1>
    <p className="mt-3 text-neutral-500 dark:text-neutral-400">
      Last updated June 2026
    </p>

    <div className="mt-10 space-y-10">
      {SECTIONS.map((section) => (
        <section key={section.title}>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
            {section.title}
          </h2>
          <p className="mt-3 leading-relaxed text-neutral-600 dark:text-neutral-300">
            {section.body}
          </p>
        </section>
      ))}
    </div>
  </div>
);

export default TermsPage;
