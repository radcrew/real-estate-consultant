import { Suspense } from "react";

import { SearchResultsView } from "@components/search-results/search-results-view";

const ResultsFallback = () => (
  <div className="mx-auto max-w-screen-xl px-4 py-16 text-center text-muted-foreground">
    Loading results…
  </div>
);

export default function SearchResultsPage() {
  return (
    <Suspense fallback={<ResultsFallback />}>
      <SearchResultsView />
    </Suspense>
  );
}
