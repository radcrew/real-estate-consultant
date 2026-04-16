import { Header } from "@/components/landing/header";

const MarketingLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col">
    <Header />
    {children}
  </div>
)

export default MarketingLayout
