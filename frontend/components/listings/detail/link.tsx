import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@utils/common";

export const ListingBackLink = () => (
  <div className="mb-6 flex flex-wrap items-center gap-3">
    <Link
      href="/listings"
      className={cn(
        buttonVariants({ variant: "ghost", size: "sm" }),
        "gap-1.5 pl-0 text-muted-foreground no-underline hover:text-foreground",
      )}
    >
      <ArrowLeft className="size-4" aria-hidden />
      Listings
    </Link>
  </div>
);
