import Image from "next/image";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";

/**
 * 404 page, ported from Voyager's `not-found.tsx`: centered 404 art, a message,
 * and a "Return home" CTA.
 */
const NotFound = () => (
  <div className="relative mx-auto max-w-screen-xl px-4 pb-16 pt-5 lg:pb-20">
    <header className="mx-auto max-w-2xl space-y-2 text-center">
      <Image
        src="/images/404.png"
        width={1500}
        height={1000}
        alt="Page not found"
        className="mx-auto h-auto w-full max-w-xl"
        priority
      />
      <span className="block text-sm font-medium tracking-wider text-neutral-800 sm:text-base dark:text-neutral-200">
        THE PAGE YOU WERE LOOKING FOR DOESN&rsquo;T EXIST.
      </span>
      <div className="pt-8">
        <ButtonPrimary href="/">Return home</ButtonPrimary>
      </div>
    </header>
  </div>
);

export default NotFound;
