import { CreProfessionals } from "@/components/landing/cre-professionals";
import { FeaturedListings } from "@/components/landing/featured-listings";
import { Hero } from "@/components/landing/hero";

const HomePage = () => (
  <main className="flex flex-1 flex-col bg-background">
    <Hero />
    <FeaturedListings />
    <CreProfessionals />
  </main>
)

export default HomePage
