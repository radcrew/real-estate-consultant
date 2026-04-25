"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

import { Button, buttonVariants } from "@components/ui/button";
import { useAuth } from "@contexts/auth";
import { cn } from "@lib/utils";

const HERO_ACTIONS_ROW = "mt-8 flex flex-wrap items-center justify-center gap-3";

const HERO_PRIMARY_ACTION_EXTRA =
  "inline-flex h-11 min-h-11 items-center gap-2.5 px-7 text-base font-semibold shadow-none";

const HERO_OUTLINE_ACTION_EXTRA =
  "h-11 min-h-11 border-border bg-background px-7 text-base font-semibold shadow-none";

export const HeroActions = () => {
  const router = useRouter();
  const { session, ready } = useAuth();
  const showSignIn = ready && !session;

  return (
    <div className={HERO_ACTIONS_ROW}>
      <Button
        size="lg"
        onClick={() => router.push("/questionnaire")}
        className={cn(HERO_PRIMARY_ACTION_EXTRA)}
      >
        <Search className="size-5 shrink-0" aria-hidden />
        Start Searching
      </Button>

      {showSignIn && (
        <Link
          href="/sign-in"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            HERO_OUTLINE_ACTION_EXTRA,
          )}
        >
          Sign In
        </Link>
      )}
    </div>
  );
};
