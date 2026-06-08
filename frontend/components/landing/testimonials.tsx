import { Quote } from "lucide-react";

import { SectionHeading } from "@components/landing/section-heading";
import { Avatar } from "@components/ui/avatar";

/**
 * "What clients say" testimonials, adapted from Voyager's `SectionClientSay`.
 * Voyager's framer-motion + react-swipeable carousel is replaced with a clean
 * static grid (no extra deps); avatars use the initial-based `Avatar` atom.
 */
const TESTIMONIALS = [
  {
    id: "1",
    name: "Tiana Abie",
    role: "Tenant rep · Chicago",
    content:
      "RadEstate's fit scoring cut our shortlist from forty buildings to six that actually matched our specs. Saved us weeks.",
  },
  {
    id: "2",
    name: "Lennie Swiffan",
    role: "Industrial broker · NW Indiana",
    content:
      "The clear-height transparency is the killer feature — no more wasted tours on buildings that don't fit the racking.",
  },
  {
    id: "3",
    name: "Berta Emili",
    role: "Investor · Indianapolis",
    content:
      "Outreach drafts in seconds, and I still get to edit before sending. It respects how brokers actually work.",
  },
];

type TestimonialsProps = {
  className?: string;
};

export const Testimonials = ({ className }: TestimonialsProps) => (
  <div className={className}>
    <SectionHeading isCenter desc="Why CRE professionals choose RadEstate.">
      What clients say
    </SectionHeading>

    <div className="grid gap-6 md:grid-cols-3 xl:gap-8">
      {TESTIMONIALS.map((item) => (
        <figure
          key={item.id}
          className="flex flex-col rounded-2xl border border-neutral-200 bg-white p-6 dark:border-neutral-700 dark:bg-neutral-900"
        >
          <Quote className="size-7 text-primary-600" aria-hidden />
          <blockquote className="mt-4 flex-1 text-neutral-700 dark:text-neutral-300">
            {item.content}
          </blockquote>
          <figcaption className="mt-6 flex items-center gap-3">
            <Avatar userName={item.name} sizeClass="h-10 w-10 text-sm" />
            <div>
              <div className="font-medium text-neutral-900 dark:text-neutral-100">
                {item.name}
              </div>
              <div className="text-sm text-neutral-500 dark:text-neutral-400">
                {item.role}
              </div>
            </div>
          </figcaption>
        </figure>
      ))}
    </div>
  </div>
);
