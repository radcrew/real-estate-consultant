"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";

import { Button, buttonVariants } from "@components/ui/button";
import { useAuth } from "@contexts/auth";
import { cn } from "@lib/utils";

import { styles } from "./styles";

export const HeroActions = () => {
  const router = useRouter();
  const { session, ready } = useAuth();
  const showSignIn = ready && !session;

  return (
    <div className={styles.row}>
      <Button
        size="lg"
        onClick={() => router.push("/questionnaire")}
        className={cn(styles.primaryAction)}
      >
        <Search className="size-5 shrink-0" aria-hidden />
        Start Searching
      </Button>

      {showSignIn && (
        <Link
          href="/sign-in"
          className={cn(
            buttonVariants({ variant: "outline", size: "lg" }),
            styles.outlineAction,
          )}
        >
          Sign In
        </Link>
      )}
    </div>
  );
};
