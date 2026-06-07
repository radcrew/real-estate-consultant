import { ContactUs } from "@components/landing/contact";
import { CreProfessionals } from "@components/landing/cre-professionals";
import { FeaturedListings } from "@components/landing/featured-listings";
import { SectionHero2 } from "@components/landing/hero2";
import { HowItWorks } from "@components/landing/how-it-works";
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
    </div>
    <CreProfessionals />
    <ContactUs />
  </main>
)

export default HomePage
