import Link from "next/link";
import { Building2 } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Header = () => (
  <header className="sticky top-0 z-40 border-b border-border bg-background">
    <div className="mx-auto flex h-16 max-w-screen-xl items-center justify-between gap-4 px-4">
      <Link
        href="/"
        className="flex min-w-0 items-center gap-2 text-lg font-bold text-primary"
      >
        <Building2 className="size-6 shrink-0" aria-hidden />
        RadEstate
      </Link>
      <div className="flex shrink-0 items-center gap-3 sm:gap-4">
        <Link
          href="/sign-in"
          className="text-sm font-semibold text-foreground transition-colors hover:text-foreground/80"
        >
          Sign In
        </Link>
        <Link
          href="/sign-up"
          className={cn(
            buttonVariants({ size: "default" }),
            "px-4 font-semibold shadow-none"
          )}
        >
          Get Started
        </Link>
      </div>
    </div>
  </header>
)
