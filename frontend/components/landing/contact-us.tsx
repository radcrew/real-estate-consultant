import { Mail } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const SECTION =
  "border-b border-border/60 bg-background px-4 py-14 sm:py-16";

const INNER =
  "mx-auto flex max-w-xl flex-col items-center gap-5 text-center sm:gap-6";

const ICON_WRAP =
  "inline-flex rounded-lg bg-primary/15 p-2.5 text-primary sm:p-3";

const HEADING =
  "text-2xl font-bold tracking-tight text-foreground sm:text-3xl";

const DESCRIPTION =
  "max-w-lg text-pretty text-sm leading-relaxed text-muted-foreground sm:text-base";

const BUTTON =
  "px-8 py-2.5 text-base font-semibold shadow-none sm:px-10 sm:py-3";

export const ContactUs = () => (
  <section
    className={SECTION}
    aria-labelledby="contact-us-heading"
  >
    <div className={INNER}>
      <div className={ICON_WRAP} aria-hidden>
        <Mail className="size-5 sm:size-6" />
      </div>
      <h2 id="contact-us-heading" className={HEADING}>
        Questions about RadEstate?
      </h2>
      <p className={DESCRIPTION}>
        Whether you need a walkthrough, enterprise options, or help with a
        listing, our team can point you in the right direction.
      </p>
      <Link
        href="/contact"
        className={cn(buttonVariants({ size: "lg" }), BUTTON)}
      >
        Contact us
      </Link>
    </div>
  </section>
);
