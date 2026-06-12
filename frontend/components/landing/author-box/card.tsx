import Link from "next/link";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

import { Avatar } from "@components/ui/avatar";

import type { AuthorBox } from "./data";

/**
 * Broker card, ported from Voyager's `CardAuthorBox2`: cover image, count chip,
 * a notched avatar cutout, name + specialty. Uses the ported `Avatar` atom.
 */
type CardBrokerProps = {
  broker: AuthorBox;
};

export const CardBroker = ({ broker }: CardBrokerProps) => (
  <Link
    href={broker.href}
    className="flex flex-col overflow-hidden rounded-3xl bg-white transition-shadow hover:shadow-xl dark:bg-neutral-900"
  >
    <div className="relative flex-shrink-0">
      <div className="relative aspect-[7/3] w-full md:aspect-[7/4]">
        <Image
          fill
          alt=""
          aria-hidden
          src={broker.bgImage}
          className="object-cover"
          sizes="(max-width: 400px) 100vw, 400px"
        />
      </div>
      <div className="absolute inset-x-3 top-3 flex">
        <div className="flex items-center justify-center rounded-full bg-neutral-100 px-4 py-1 text-xs font-medium leading-none dark:bg-neutral-800">
          {broker.count.toLocaleString("en-US")}
          <ArrowRight className="ml-3 size-5 text-primary-600" aria-hidden />
        </div>
      </div>
    </div>

    <div className="relative flex -translate-y-7 flex-col items-center px-6 pt-px text-center">
      <svg
        className="h-12 text-white dark:text-neutral-900"
        viewBox="0 0 135 54"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden
      >
        <path
          d="M101.911 19.8581C99.4421 17.4194 97.15 14.8065 94.6816 12.1935C94.3289 11.671 93.8 11.3226 93.271 10.8C92.9184 10.4516 92.7421 10.2774 92.3895 9.92903C85.8658 3.83226 76.8737 0 67.1763 0C57.4789 0 48.4868 3.83226 41.7868 9.92903C41.4342 10.2774 41.2579 10.4516 40.9053 10.8C40.3763 11.3226 40.0237 11.671 39.4947 12.1935C37.0263 14.8065 34.7342 17.4194 32.2658 19.8581C23.45 28.7419 11.6368 30.4839 0 30.8323V54H16.5737H32.2658H101.734H110.374H134.176V30.6581C122.539 30.3097 110.726 28.7419 101.911 19.8581Z"
          fill="currentColor"
        />
      </svg>
      <span className="absolute top-2">
        <Avatar
          sizeClass="w-12 h-12 text-2xl"
          radius="rounded-full"
          imgUrl={broker.avatar}
          userName={broker.displayName}
        />
      </span>
      <div className="mt-6">
        <h2 className="text-base font-medium">
          <span className="line-clamp-1">{broker.displayName}</span>
        </h2>
        <span className="mt-1 block text-sm text-neutral-500 dark:text-neutral-400">
          @{broker.jobName}
        </span>
      </div>
    </div>
  </Link>
);
