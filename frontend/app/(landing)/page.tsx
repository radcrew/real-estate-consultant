import { CategorySlider } from "@components/landing/category-slider";
import {
  DISCOVERY_CATEGORIES,
  PROPERTY_TYPE_CATEGORIES,
} from "@components/landing/category-slider/data";
import { ContactUs } from "@components/landing/contact";
import { CreProfessionals } from "@components/landing/cre-professionals";
import { DownloadApp } from "@components/landing/download-app";
import { FeaturedListings } from "@components/landing/featured-listings";
import { SectionHero2 } from "@components/landing/hero2";
import { HowItWorks } from "@components/landing/how-it-works";
import { OurFeatures } from "@components/landing/our-features";
import { PartnerLogos } from "@components/landing/partner-logos";
import { BackgroundSection } from "@components/voyager/background-section";

const HomePage = () => (
  <main className="relative flex flex-1 flex-col overflow-hidden bg-background">
    <div className="mx-auto w-full max-w-screen-xl space-y-24 px-4 pb-24 lg:space-y-28 lg:pb-28">
      <SectionHero2 />
      <PartnerLogos />
      <HowItWorks />

      <div className="relative py-16">
        <BackgroundSection />
        <FeaturedListings />
      </div>

      <OurFeatures />

      <DownloadApp />

      <CategorySlider
        heading="Suggestions for discovery"
        subHeading="Popular markets RadEstate recommends for you"
        categories={DISCOVERY_CATEGORIES}
        cardType="card4"
        slideClassName="basis-1/2 sm:basis-1/3 lg:basis-1/4"
      />

      <CategorySlider
        heading="Explore by property type"
        subHeading="Browse commercial inventory across asset classes"
        categories={PROPERTY_TYPE_CATEGORIES}
        cardType="card5"
        slideClassName="basis-1/2 sm:basis-1/3 lg:basis-1/4 xl:basis-1/5"
      />
    </div>
    <CreProfessionals />
    <ContactUs />
  </main>
)

export default HomePage
