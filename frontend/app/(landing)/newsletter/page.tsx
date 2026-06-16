import type { Metadata } from "next";

import { Subscribe } from "@components/landing/subscribe";

export const metadata: Metadata = {
  title: "Newsletter",
  description:
    "Subscribe to the RadEstate newsletter for new commercial listings, market intelligence, and CRE insights.",
};

const NewsletterPage = () => (
  <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
    <div className="max-w-2xl">
      <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
        Newsletter
      </h1>
      <p className="mt-3 text-neutral-500 dark:text-neutral-400">
        Stay ahead of the market — subscribe for new commercial listings,
        submarket pricing trends, and CRE insights delivered to your inbox.
      </p>
    </div>

    <Subscribe className="mt-12" />
  </div>
);

export default NewsletterPage;
