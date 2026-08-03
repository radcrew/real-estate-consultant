import { Suspense } from "react";

import { SearchResults } from "@components/search/result";
import { PAGE_CONTAINER } from "@components/ui/styles";
import { cn } from "@utils/common";

const ResultsFallback = () => (
  <div className={cn(PAGE_CONTAINER, "py-16 text-center text-muted-foreground")}>
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
