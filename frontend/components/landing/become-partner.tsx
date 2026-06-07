import Image from "next/image";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { Logo } from "@components/ui/voyager/logo";
import { cn } from "@utils/common";

/**
 * "Become a partner" CTA banner, ported from Voyager's `SectionBecomeAnAuthor`.
 * Copy adapted to RadEstate (list your property / partner with us).
 */
type BecomePartnerProps = {
  className?: string;
};

export const BecomePartner = ({ className }: BecomePartnerProps) => (
  <div className={cn("relative flex flex-col items-center lg:flex-row", className)}>
    <div className="mb-16 flex-shrink-0 lg:mb-0 lg:mr-10 lg:w-2/5">
      <Logo className="text-xl" />
      <h2 className="mt-6 text-3xl font-semibold sm:mt-11 sm:text-4xl">
        List your property with RadEstate
      </h2>
      <span className="mt-6 block text-neutral-500 dark:text-neutral-400">
        Reach qualified tenants and buyers searching with AI-powered fit scoring.
        Put your commercial listings in front of the right people, faster.
      </span>
      <ButtonPrimary href="/sign-up" className="mt-6 sm:mt-11">
        Become a partner
      </ButtonPrimary>
    </div>
    <div className="flex-grow">
      <Image
        src="/images/BecomeAnAuthorImg.png"
        width={890}
        height={694}
        alt=""
        aria-hidden
        className="h-auto w-full"
      />
    </div>
  </div>
);
