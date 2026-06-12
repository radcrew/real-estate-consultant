"use client";

import { useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { Input } from "@components/ui/input";
import { Textarea } from "@components/ui/textarea";

const LABEL = "text-sm font-medium text-neutral-700 dark:text-neutral-300";

/**
 * Contact form, ported from Voyager's contact page form. No contact backend
 * exists, so it submits locally (shows a confirmation) — presentation only.
 */
export const ContactForm = () => {
  const [sent, setSent] = useState(false);

  if (sent) {
    return (
      <p
        className="rounded-2xl border border-neutral-200 bg-neutral-50 px-5 py-4 text-sm text-neutral-700 dark:border-neutral-700 dark:bg-neutral-800/50 dark:text-neutral-200"
        role="status"
      >
        Thanks for reaching out — we&rsquo;ll get back to you shortly.
      </p>
    );
  }

  return (
    <form
      className="grid grid-cols-1 gap-6"
      onSubmit={(e) => {
        e.preventDefault();
        setSent(true);
      }}
    >
      <label className="block">
        <span className={LABEL}>Full name</span>
        <Input required placeholder="Example Doe" type="text" className="mt-1" />
      </label>
      <label className="block">
        <span className={LABEL}>Email address</span>
        <Input
          required
          type="email"
          placeholder="example@example.com"
          className="mt-1"
        />
      </label>
      <label className="block">
        <span className={LABEL}>Message</span>
        <Textarea required className="mt-1" rows={6} />
      </label>
      <div>
        <ButtonPrimary type="submit">Send Message</ButtonPrimary>
      </div>
    </form>
  );
};
