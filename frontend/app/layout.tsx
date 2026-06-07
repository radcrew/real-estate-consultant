import type { Metadata } from "next";
import { Geist_Mono, Poppins } from "next/font/google";

import { Header } from "@components/landing/header";
import { SavedListingsProvider } from "@components/saved/provider";
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
  title: {
    default: "RadEstate",
    template: "%s · RadEstate",
  },
  description: "RadEstate real estate consultant platform",
};

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => (
  <html
    lang="en"
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
