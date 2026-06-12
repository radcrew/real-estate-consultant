import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How RadEstate handles your data",
};

const SECTIONS = [
  {
    title: "Information we collect",
    body: "We collect the account details you provide (name, email, contact info) and the search criteria you enter so we can match you with relevant commercial listings.",
  },
  {
    title: "How we use it",
    body: "Your data powers AI fit scoring, saved searches, and broker outreach drafts. We do not sell your personal information.",
  },
  {
    title: "Outreach",
    body: "Outreach drafts are generated for your review. Nothing is sent on your behalf without your explicit action.",
  },
  {
    title: "Your choices",
    body: "You can update or delete your profile information at any time from your account. Contact us with any questions about your data.",
  },
];

const PrivacyPage = () => (
  <div className="mx-auto max-w-3xl px-4 py-16 lg:py-24">
    <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
      Privacy Policy
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

export default PrivacyPage;
