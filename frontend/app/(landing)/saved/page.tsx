import type { Metadata } from "next";

import { SavedView } from "@components/saved/view";

export const metadata: Metadata = {
  title: "Saved properties",
  description: "Commercial properties you've saved on RadEstate.",
};

const SavedPage = () => <SavedView />;

export default SavedPage;
