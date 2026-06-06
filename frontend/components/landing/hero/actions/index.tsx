"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { ButtonThird } from "@components/ui/voyager/button-third";
import { useAuth } from "@contexts/auth";

import { STYLES } from "./styles";

export const HeroActions = () => {
  const router = useRouter();
  const { session, ready } = useAuth();
  const showSignIn = ready && !session;

  return (
    <div className={STYLES.row}>
      <ButtonPrimary
        onClick={() => router.push("/questionnaire")}
        sizeClass="px-7 py-3.5"
        fontSize="text-base font-medium"
      >
        <Search className="mr-2.5 size-5 shrink-0" aria-hidden />
        Start Searching
      </ButtonPrimary>

      {showSignIn && (
        <ButtonThird
          href="/sign-in"
          sizeClass="px-7 py-3.5"
          fontSize="text-base font-medium"
        >
          Sign In
        </ButtonThird>
      )}
    </div>
  );
};
