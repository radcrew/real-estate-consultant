import Image from "next/image";

import { Badge } from "@components/ui/voyager/badge";
import { cn } from "@utils/common";

/**
 * "Our features" / benefits section, ported from Voyager's `SectionOurFeatures`
 * (home-2 `type2` = image-reversed). Copy adapted to RadEstate's CRE value
 * props; uses the ported `Badge` atom for the colored labels.
 */
const FEATURES = [
  {
    badge: "Scoring",
    color: "blue" as const,
    title: "AI fit scoring",
    desc: "Every property is ranked 0–100 against your exact requirements — no more manual filtering.",
  },
  {
    badge: "Coverage",
    color: "green" as const,
    title: "Search the whole market",
    desc: "Broker-style search across submarkets surfaces inventory you'd otherwise miss.",
  },
  {
    badge: "Outreach",
    color: "red" as const,
    title: "Secure and simple",
    desc: "Generate broker outreach drafts in seconds and edit before sending — you stay in control.",
  },
];

type OurFeaturesProps = {
  className?: string;
};

export const OurFeatures = ({ className }: OurFeaturesProps) => (
  <div
    className={cn(
      "relative flex flex-col items-center lg:flex-row-reverse lg:py-14",
      className,
    )}
  >
    <div className="flex-grow">
      <Image
        src="/images/our-features-2.png"
        width={825}
        height={820}
        alt=""
        aria-hidden
        className="h-auto w-full"
      />
    </div>

    <div className="mt-10 max-w-2xl flex-shrink-0 lg:mt-0 lg:w-2/5 lg:pr-16">
      <span className="text-sm uppercase tracking-widest text-neutral-400">
        Benefits
      </span>
      <h2 className="mt-5 text-4xl font-semibold">Built for CRE professionals</h2>

      <ul className="mt-16 space-y-10">
        {FEATURES.map((feature) => (
          <li key={feature.title} className="space-y-4">
            <Badge name={feature.badge} color={feature.color} />
            <span className="block text-xl font-semibold">{feature.title}</span>
            <span className="mt-5 block text-neutral-500 dark:text-neutral-400">
              {feature.desc}
            </span>
          </li>
        ))}
      </ul>
    </div>
  </div>
);
