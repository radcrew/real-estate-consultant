import { Footer } from "@components/landing/footer";

const LandingLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <div className="flex min-h-screen flex-col">
    {children}
    <Footer />
  </div>
)

export default LandingLayout
