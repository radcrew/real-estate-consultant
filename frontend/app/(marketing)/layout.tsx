import { SiteHeader } from "@/components/landing/site-header";

const MarketingLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col">
    <SiteHeader />
    {children}
  </div>
)

export default MarketingLayout
