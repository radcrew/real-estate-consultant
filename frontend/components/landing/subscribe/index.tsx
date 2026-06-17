"use client";

import { type FormEvent, useState } from "react";
import Image from "next/image";
import { ArrowRight } from "lucide-react";

import { Badge } from "@components/ui/badge";
import { ButtonCircle } from "@components/ui/button-circle";
import { Input } from "@components/ui/input";
import { useToast } from "@components/ui/toast";
import { cn } from "@utils/common";

/**
 * Newsletter section, ported from Voyager's `SectionSubscribe2`. Submits to the
 * `/api/newsletter` route handler, which adds the email to the Buttondown list
 * server-side (keeping the Buttondown API key off the client).
 */
type SubscribeProps = {
  className?: string;
};

export const Subscribe = ({ className }: SubscribeProps) => {
  const { showError } = useToast();
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [subscribed, setSubscribed] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await fetch("/api/newsletter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data: { ok?: boolean; error?: string } = await res
        .json()
        .catch(() => ({}));

      if (!res.ok || !data.ok) {
        showError(data.error || "Could not subscribe. Please try again.");
        return;
      }

      setSubscribed(true);
    } catch {
      showError("Could not reach the newsletter service. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={cn("relative flex flex-col lg:flex-row lg:items-center", className)}>
      <div className="mb-10 flex-shrink-0 lg:mb-0 lg:mr-10 lg:w-2/5">
        <h2 className="text-4xl font-semibold">Join our newsletter 🎉</h2>
        <span className="mt-5 block text-neutral-500 dark:text-neutral-400">
          New commercial listings, market intelligence, and CRE insights —
          delivered to your inbox.
        </span>
        <ul className="mt-10 space-y-4">
          <li className="flex items-center space-x-4">
            <Badge name="01" />
            <span className="font-medium text-neutral-700 dark:text-neutral-300">
              New inventory alerts
            </span>
          </li>
          <li className="flex items-center space-x-4">
            <Badge color="red" name="02" />
            <span className="font-medium text-neutral-700 dark:text-neutral-300">
              Submarket pricing trends
            </span>
          </li>
        </ul>

        {subscribed ? (
          <p className="mt-10 text-sm font-medium text-primary-600" role="status">
            Thanks for subscribing!
          </p>
        ) : (
          <form className="relative mt-10 max-w-sm" onSubmit={handleSubmit}>
            <Input
              required
              aria-required
              placeholder="Enter your email"
              type="email"
              rounded="rounded-full"
              sizeClass="h-12 px-5 py-3"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
            />
            <ButtonCircle
              type="submit"
              className="absolute right-1.5 top-1/2 -translate-y-1/2"
              size="w-10 h-10"
              aria-label="Subscribe"
              disabled={submitting}
            >
              <ArrowRight className="size-5" aria-hidden />
            </ButtonCircle>
          </form>
        )}
      </div>
      <div className="flex-grow">
        <Image
          src="/images/SVG-subcribe2.png"
          width={1120}
          height={803}
          alt=""
          aria-hidden
          className="h-auto w-full"
        />
      </div>
    </div>
  );
};
