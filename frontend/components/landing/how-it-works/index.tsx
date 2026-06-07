import Image from "next/image";

import { SectionHeading } from "@components/landing/section-heading";

/**
 * "How it works" section, ported from Voyager's `SectionHowItWork` (home-2
 * variant). Uses the real-estate step copy and the `HIW2-*` light/dark art,
 * with the dashed `VectorHIW` connector behind the row on md+.
 */
const STEPS = [
  {
    id: 1,
    img: "/images/HIW2-1.png",
    imgDark: "/images/HIW2-1-dark.png",
    title: "Smart search",
    desc: "Name the area or type of property you're looking for. Our app finds you the perfect match.",
  },
  {
    id: 2,
    img: "/images/HIW2-2.png",
    imgDark: "/images/HIW2-2-dark.png",
    title: "Choose property",
    desc: "From the options our app provides, select any property you'd like to explore in detail.",
  },
  {
    id: 3,
    img: "/images/HIW2-3.png",
    imgDark: "/images/HIW2-3-dark.png",
    title: "Reach the broker",
    desc: "Generate outreach in seconds — enter your location, property type and price range to start.",
  },
] as const;

export const HowItWorks = () => (
  <div>
    <SectionHeading isCenter desc="From smart search to broker outreach" className="text-neutral-900 dark:text-neutral-50">
      How it works
    </SectionHeading>

    <div className="relative mt-20 grid gap-20 md:grid-cols-3">
      <Image
        className="absolute inset-x-0 top-10 hidden md:block"
        src="/images/VectorHIW.svg"
        width={1431}
        height={105}
        alt=""
        aria-hidden
        unoptimized
      />
      {STEPS.map((step) => (
        <div
          key={step.id}
          className="relative mx-auto flex max-w-xs flex-col items-center"
        >
          <Image
            className="mx-auto mb-8 block max-w-[180px] dark:hidden"
            src={step.img}
            width={293}
            height={269}
            alt=""
            aria-hidden
          />
          <Image
            className="mx-auto mb-8 hidden max-w-[180px] dark:block"
            src={step.imgDark}
            width={293}
            height={269}
            alt=""
            aria-hidden
          />
          <div className="mt-auto text-center">
            <h3 className="text-xl font-semibold">{step.title}</h3>
            <span className="mt-5 block text-neutral-500 dark:text-neutral-400">
              {step.desc}
            </span>
          </div>
        </div>
      ))}
    </div>
  </div>
);
