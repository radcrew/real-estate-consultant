import { SectionHeading } from "@components/landing/section-heading";
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

  </div>
);
