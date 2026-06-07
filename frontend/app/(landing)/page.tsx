import { ContactUs } from "@components/landing/contact";
import { CreProfessionals } from "@components/landing/cre-professionals";
import { FeaturedListings } from "@components/landing/featured-listings";
import { SectionHero2 } from "@components/landing/hero2";

const HomePage = () => (
  <main className="relative flex flex-1 flex-col overflow-hidden bg-background">
    <div className="mx-auto w-full max-w-screen-xl px-4">
      <SectionHero2 />
    </div>
    <FeaturedListings />
    <CreProfessionals />
    <ContactUs />
  </main>
)

export default HomePage
