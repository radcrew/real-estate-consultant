import { SectionHeading } from "@components/landing/section-heading";
import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { ButtonSecondary } from "@components/ui/voyager/button-secondary";
import { cn } from "@utils/common";

import { CardBroker } from "./card";
import { TOP_BROKERS } from "./data";

/**
 * "Top brokers" grid, ported from Voyager's `SectionGridAuthorBox` (box2
 * variant). Travel "authors/hosts" concept adapted to CRE brokers.
 */
type BrokerBoxProps = {
  className?: string;
};

export const BrokerBox = ({ className }: BrokerBoxProps) => (
  <div className={cn("relative", className)}>
    <SectionHeading isCenter desc="Ranked by active commercial listings">
      Top brokers this month
    </SectionHeading>

    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 md:gap-8 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      {TOP_BROKERS.map((broker) => (
        <CardBroker key={broker.id} broker={broker} />
      ))}
    </div>

    <div className="mt-16 flex flex-col justify-center space-y-3 sm:flex-row sm:space-x-5 sm:space-y-0">
      <ButtonSecondary href="/listings">Show me more</ButtonSecondary>
      <ButtonPrimary href="/sign-up">Become a partner</ButtonPrimary>
    </div>
  </div>
);
