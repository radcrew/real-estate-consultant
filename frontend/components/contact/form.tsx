"use client";

import { type FormEvent, useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { Input } from "@components/ui/input";
import { Textarea } from "@components/ui/textarea";
import { useToast } from "@components/ui/toast";
import { WEB3FORMS_ACCESS_KEY } from "@config/env";

const LABEL = "text-sm font-medium text-neutral-700 dark:text-neutral-300";

/**
 * Contact form. Submits to Web3Forms (https://web3forms.com), which emails the
 * message to the inbox tied to NEXT_PUBLIC_WEB3FORMS_ACCESS_KEY — no backend
 * endpoint required.
 */
export const ContactForm = () => {
  const { showError } = useToast();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!WEB3FORMS_ACCESS_KEY) {
      showError("The contact form isn't configured yet. Please email us directly.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("https://api.web3forms.com/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          access_key: WEB3FORMS_ACCESS_KEY,
          subject: "New contact message from RadEstate",
          from_name: "RadEstate Contact Form",
          name: name.trim(),
          email: email.trim(),
          message: message.trim(),
        }),
      });

      const data: { success?: boolean; message?: string } = await res
        .json()
        .catch(() => ({}));

      if (!res.ok || !data.success) {
        showError(data.message || "Could not send your message. Please try again.");
        return;
      }

      setSent(true);
    } catch {
      showError(
        "Could not reach the contact service. Please check your connection and try again.",
      );
    } finally {
      setSubmitting(false);
    }
  };

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
    <form className="grid grid-cols-1 gap-6" onSubmit={handleSubmit}>
      <label className="block">
        <span className={LABEL}>Full name</span>
        <Input
          required
          name="name"
          autoComplete="name"
          placeholder="Example Doe"
          type="text"
          className="mt-1"
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={submitting}
        />
      </label>
      <label className="block">
        <span className={LABEL}>Email address</span>
        <Input
          required
          name="email"
          autoComplete="email"
          type="email"
          placeholder="example@example.com"
          className="mt-1"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={submitting}
        />
      </label>
      <label className="block">
        <span className={LABEL}>Message</span>
        <Textarea
          required
          name="message"
          className="mt-1"
          rows={6}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          disabled={submitting}
        />
      </label>
      <div>
        <ButtonPrimary type="submit" disabled={submitting} loading={submitting}>
          {submitting ? "Sending…" : "Send Message"}
        </ButtonPrimary>
      </div>
    </form>
  );
};
