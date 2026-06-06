import { ContactUs } from "@components/landing/contact";
import { CreProfessionals } from "@components/landing/cre-professionals";
import { FeaturedListings } from "@components/landing/featured-listings";
import { Hero } from "@components/landing/hero";
// TEMP: Voyager atom visual check — remove after confirming the look.
import { ButtonPrimary } from "@components/ui/voyager/button-primary";

const HomePage = () => (
  <main className="flex flex-1 flex-col bg-background">
    {/* TEMP: Voyager ButtonPrimary preview — delete this block when done. */}
    <div className="flex items-center gap-4 p-8">
      <ButtonPrimary>Voyager primary button</ButtonPrimary>
      <ButtonPrimary loading>Loading state</ButtonPrimary>
    </div>
    <Hero />
    <FeaturedListings />
    <CreProfessionals />
    <ContactUs />
  </main>
)

export default HomePage
