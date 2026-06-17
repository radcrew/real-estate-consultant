import type { Metadata } from "next";

import { ContactForm } from "@components/contact/form";
import { SocialsList } from "@components/ui/socials-list";

export const metadata: Metadata = {
  title: "Contact",
  description: "Get in touch with RadEstate",
};

const INFO_HEADING = "text-sm font-semibold uppercase tracking-wider dark:text-neutral-200";

const INFO = [
  {
    title: "🗺 ADDRESS",
    desc: "200 W Madison St, Suite 2100, Chicago, IL 60606",
  },
  {
    title: "💌 EMAIL",
    desc: "hello@radestate.com",
  },
  {
    title: "☎ PHONE",
    desc: "(312) 555-0142",
  },
];

const ContactPage = () => (
  <div className="overflow-hidden">
    <div className="mb-24 lg:mb-32">
      <h2 className="my-16 flex items-center justify-center text-3xl font-semibold leading-[115%] text-neutral-900 sm:my-20 md:text-5xl md:leading-[115%] dark:text-neutral-100">
        Contact
      </h2>
      <div className="mx-auto max-w-7xl px-4">
        <div className="grid flex-shrink-0 grid-cols-1 gap-12 sm:grid-cols-2">
          <div className="max-w-sm space-y-8">
            {INFO.map((item) => (
              <div key={item.title}>
                <h3 className={INFO_HEADING}>
                  {item.title}
                </h3>
                <span className="mt-2 block text-neutral-500 dark:text-neutral-400">
                  {item.desc}
                </span>
              </div>
            ))}
            <div>
              <h3 className={INFO_HEADING}>
                🌏 SOCIALS
              </h3>
              <SocialsList className="mt-2" />
            </div>
          </div>
          <div>
            <ContactForm />
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default ContactPage;
