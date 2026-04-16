import Link from "next/link";
import { Building2 } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const SiteHeader = () => (
  <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
    <div className="mx-auto flex h-16 max-w-screen-xl items-center justify-between px-4">
      <Link
        href="/"
        className="flex items-center gap-2 text-lg font-bold text-primary"
      >
        <Building2 className="size-6 shrink-0" aria-hidden />
        RadEstate
      </Link>
      <div className="flex items-center gap-2">
        <Link
          href="/sign-in"
          className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
        >
          Sign In
        </Link>
        <Link
          href="/sign-up"
          className={cn(buttonVariants({ size: "sm" }))}
        >
          Get Started
        </Link>
      </div>
    </div>
  </header>
)
