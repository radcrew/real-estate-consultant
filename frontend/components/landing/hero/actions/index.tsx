"use client";

import { Search } from "lucide-react";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { ButtonThird } from "@components/ui/voyager/button-third";
import { brand } from "@config/brand";
import { useAuth } from "@contexts/auth";

import { STYLES } from "./styles";

export const HeroActions = () => {
  const { session, ready } = useAuth();
  const showSignIn = ready && !session;

  return (
    <div className={STYLES.row}>
      <ButtonPrimary
        href={brand.hero.primaryCta.href}
        sizeClass="px-7 py-3.5"
        fontSize="text-base font-medium"
      >
        <Search className="mr-2.5 size-5 shrink-0" aria-hidden />
        {brand.hero.primaryCta.label}
      </ButtonPrimary>

      {showSignIn && (
        <ButtonThird
          href={brand.hero.secondaryCta.href}
          sizeClass="px-7 py-3.5"
          fontSize="text-base font-medium"
        >
          {brand.hero.secondaryCta.label}
        </ButtonThird>
      )}
    </div>
  );
};
