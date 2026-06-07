import type { Metadata } from "next";
import Image from "next/image";

import { SectionHeading } from "@components/landing/section-heading";
import { Subscribe } from "@components/landing/subscribe";

export const metadata: Metadata = {
  title: "About",
  description: "About RadEstate — AI-assisted commercial real estate search",
};

const FACTS = [
  { id: "1", heading: "8 markets", subHeading: "Commercial inventory tracked across major US metros and submarkets." },
  { id: "2", heading: "0–100 scoring", subHeading: "Every property ranked against your exact requirements by AI." },
  { id: "3", heading: "Seconds, not days", subHeading: "Broker outreach drafts generated instantly — you stay in control." },
];

const TEAM = [
  {
    id: "1",
    name: "Niamh O'Shea",
    job: "Co-founder & CEO",
    avatar:
      "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&auto=format&fit=crop&w=400&q=80",
  },
  {
    id: "2",
    name: "Danien Jame",
    job: "Co-founder & CTO",
    avatar:
      "https://images.unsplash.com/photo-1568602471122-7832951cc4c5?ixlib=rb-1.2.1&auto=format&fit=crop&w=400&q=80",
  },
  {
    id: "3",
    name: "Orla Dwyer",
    job: "Head of Brokerage",
    avatar:
      "https://images.unsplash.com/photo-1560365163-3e8d64e762ef?ixlib=rb-1.2.1&auto=format&fit=crop&w=400&q=80",
  },
  {
    id: "4",
    name: "Dara Frazier",
    job: "Chief Strategy Officer",
    avatar:
      "https://images.unsplash.com/photo-1580489944761-15a19d654956?ixlib=rb-1.2.1&auto=format&fit=crop&w=400&q=80",
  },
];

const AboutPage = () => (
  <div className="relative overflow-hidden">
    <div className="mx-auto max-w-screen-xl space-y-16 px-4 py-16 lg:space-y-28 lg:py-28">
      {/* Hero */}
      <div className="flex flex-col items-center space-y-14 text-center lg:flex-row lg:space-x-10 lg:space-y-0 lg:text-left">
        <div className="w-screen max-w-full space-y-5 lg:max-w-lg lg:space-y-7">
          <h2 className="text-3xl font-semibold !leading-tight text-neutral-900 md:text-4xl xl:text-5xl dark:text-neutral-100">
            👋 About RadEstate.
          </h2>
          <span className="block text-base text-neutral-500 xl:text-lg dark:text-neutral-400">
            RadEstate is an AI-assisted commercial real estate platform. We help
            tenants, buyers, and brokers find the right space faster — with
            transparent specs, fit scoring, and outreach that keeps you in control.
          </span>
        </div>
        <div className="flex-grow">
          <Image
            className="h-auto w-full"
            src="/images/about-hero-right.png"
            width={1450}
            height={638}
            alt="About RadEstate"
            priority
          />
        </div>
      </div>

      {/* Fast facts */}
      <div className="relative">
        <SectionHeading desc="What sets RadEstate apart for commercial real estate.">
          🚀 Fast facts
        </SectionHeading>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 xl:gap-8">
          {FACTS.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl bg-neutral-50 p-6 dark:bg-neutral-800"
            >
              <h3 className="text-2xl font-semibold leading-none text-neutral-900 md:text-3xl dark:text-neutral-200">
                {item.heading}
              </h3>
              <span className="mt-3 block text-sm text-neutral-500 sm:text-base dark:text-neutral-400">
                {item.subHeading}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Team */}
      <div className="relative">
        <SectionHeading desc="The people building RadEstate.">⛱ Team</SectionHeading>
        <div className="grid gap-x-5 gap-y-8 sm:grid-cols-2 lg:grid-cols-4 xl:gap-x-8">
          {TEAM.map((item) => (
            <div key={item.id} className="max-w-sm">
              <div className="relative aspect-square overflow-hidden rounded-xl">
                <Image
                  fill
                  className="object-cover"
                  src={item.avatar}
                  alt={item.name}
                  sizes="(max-width: 768px) 100vw, 30vw"
                />
              </div>
              <h3 className="mt-4 text-lg font-semibold text-neutral-900 md:text-xl dark:text-neutral-200">
                {item.name}
              </h3>
              <span className="block text-sm text-neutral-500 sm:text-base dark:text-neutral-400">
                {item.job}
              </span>
            </div>
          ))}
        </div>
      </div>

      <Subscribe />
    </div>
  </div>
);

export default AboutPage;
