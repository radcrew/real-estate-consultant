import { Footer } from "@/components/landing/footer";
import { Header } from "@/components/landing/header";

const MarketingLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col">
    <Header />
    {children}
    <Footer />
  </div>
)

export default MarketingLayout
