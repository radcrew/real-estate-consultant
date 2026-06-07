import type { Metadata } from "next";

import { ListPropertyForm } from "@components/list-property/form";

export const metadata: Metadata = {
  title: "List your property",
  description: "Submit a commercial property listing to RadEstate.",
};

const ListPropertyPage = () => (
  <div className="mx-auto max-w-3xl px-4 py-16 lg:py-20">
    <div className="mb-10">
      <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
        List your property
      </h1>
      <p className="mt-3 text-neutral-500 dark:text-neutral-400">
        Reach qualified tenants and buyers searching with AI-powered fit scoring.
      </p>
    </div>
    <ListPropertyForm />
  </div>
);

export default ListPropertyPage;
