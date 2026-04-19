import Link from "next/link";

import { buttonVariants } from "@components/ui/button";
import { cn } from "@lib/utils";

export const SignedOutNav = () => (
  <>
    <Link
      href="/sign-in"
      className="text-sm font-semibold text-foreground transition-colors hover:text-foreground/80"
    >
      Sign In
    </Link>
    <Link
      href="/sign-up"
      className={cn(buttonVariants({ size: "default" }), "px-4 font-semibold shadow-none")}
    >
      Get Started
    </Link>
  </>
);
