import { Footer } from "@components/landing/footer";
import { Header } from "@components/landing/header";

const LandingLayout = ({
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

export default LandingLayout
