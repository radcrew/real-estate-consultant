import { FeaturedListings } from "@/components/landing/featured-listings";
import { Hero } from "@/components/landing/hero";

const HomePage = () => (
  <main className="flex flex-1 flex-col bg-background">
    <Hero />
    <FeaturedListings />
  </main>
)

export default HomePage
