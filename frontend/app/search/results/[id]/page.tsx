import { Suspense } from "react";

import { SearchResults } from "@components/search-results";

const ResultsFallback = () => (
  <div className="mx-auto max-w-screen-xl px-4 py-16 text-center text-muted-foreground">
    Loading results…
  </div>
);

export default function SearchResultsByProfilePage() {
  return (
    <Suspense fallback={<ResultsFallback />}>
      <SearchResults />
    </Suspense>
  );
}
