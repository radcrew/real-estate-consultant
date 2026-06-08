import type { Metadata } from "next";
import { Geist_Mono, Poppins } from "next/font/google";

import { Header } from "@components/landing/header";
import { SavedListingsProvider } from "@components/saved/provider";
import { brand } from "@config/brand";
import { AuthProvider } from "@contexts/auth";

import "./globals.css";

// Voyager's typeface — Poppins (weights 300–700) — for visual parity.
const poppins = Poppins({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  applicationName: brand.name,
  title: {
    default: `${brand.name} · ${brand.tagline}`,
    template: `%s · ${brand.name}`,
  },
  description: brand.hero.subtitle,
  keywords: [
    "commercial real estate",
    "CRE",
    "AI property search",
    "fit scoring",
    "broker outreach",
    "real estate consultant",
  ],
  authors: [{ name: brand.name }],
  creator: brand.name,
  openGraph: {
    type: "website",
    siteName: brand.name,
    title: `${brand.name} · ${brand.tagline}`,
    description: brand.hero.subtitle,
  },
  twitter: {
    card: "summary_large_image",
    title: `${brand.name} · ${brand.tagline}`,
    description: brand.hero.subtitle,
  },
};

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <html
    lang="en"
    suppressHydrationWarning
    className={`${poppins.variable} ${geistMono.variable} h-full antialiased`}
  >
    <body className="flex min-h-full flex-col font-sans">
      {/* Apply saved theme before paint to avoid a light-mode flash on reload. */}
      <script
        dangerouslySetInnerHTML={{
          __html:
            "try{if(localStorage.theme==='dark'){document.documentElement.classList.add('dark')}}catch(e){}",
        }}
      />
      <AuthProvider>
        <SavedListingsProvider>
          <Header />
          <div className="flex min-h-0 flex-1 flex-col">{children}</div>
        </SavedListingsProvider>
      </AuthProvider>
    </body>
  </html>
)

export default RootLayout
