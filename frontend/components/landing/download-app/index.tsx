import Image from "next/image";

import { BackgroundSection } from "@components/voyager/background-section";

/**
 * "Mobile apps" CTA, ported from Voyager's `SectionDowloadApp`. Uses Voyager's
 * local art (download bg, phone mockup, decorative SVGs, store badges) and the
 * ported `BackgroundSection`. Store links are placeholders for now.
 */
export const DownloadApp = () => (
  <div className="relative pb-0 pt-24 lg:py-32 xl:py-40 2xl:py-48">
    <BackgroundSection className="bg-neutral-100/80 dark:bg-opacity-100">
      <Image
        className="absolute inset-0 size-full rounded-3xl object-cover object-right"
        src="/images/dowloadAppBG.png"
        alt=""
        aria-hidden
        fill
        sizes="100vw"
      />

      <div className="absolute bottom-0 right-0 hidden max-w-xl overflow-hidden rounded-3xl lg:block xl:max-w-2xl">
        <Image src="/images/appRightImg.png" width={2611} height={2015} alt="" aria-hidden />
      </div>
      <div className="absolute right-0 top-0 max-w-2xl">
        <Image src="/images/appRightImgTree.png" width={413} height={390} alt="" aria-hidden />
      </div>
      <div className="absolute bottom-10 left-0 max-w-2xl">
        <Image src="/images/appSvg1.png" width={334} height={121} alt="" aria-hidden />
      </div>
    </BackgroundSection>

    <div className="relative inline-block">
      <h2 className="text-5xl font-bold text-neutral-800 md:text-6xl xl:text-7xl">
        Mobile apps
      </h2>
      <span className="mt-7 block max-w-md text-neutral-600">
        Search, score, and shortlist commercial properties from anywhere. Take
        your saved profiles and broker outreach on the go.
      </span>
      <div className="mt-10 flex space-x-3 sm:mt-14">
        <a href="#" target="_blank" rel="noopener noreferrer">
          <Image src="/images/btn-ios.png" width={185} height={60} alt="Download on the App Store" />
        </a>
        <a href="#" target="_blank" rel="noopener noreferrer">
          <Image src="/images/btn-android.png" width={185} height={60} alt="Get it on Google Play" />
        </a>
      </div>

      <Image
        className="absolute z-10 hidden lg:left-full lg:top-0 lg:block lg:max-w-sm xl:top-1/2 2xl:max-w-none"
        src="/images/appSvg2.png"
        width={559}
        height={152}
        alt=""
        aria-hidden
      />

      <div className="mt-10 block max-w-2xl overflow-hidden rounded-3xl lg:hidden">
        <Image src="/images/appRightImg.png" width={2611} height={2015} alt="" aria-hidden />
      </div>
    </div>
  </div>
);
