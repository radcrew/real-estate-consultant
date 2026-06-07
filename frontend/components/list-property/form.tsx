"use client";

import { useState } from "react";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";
import { Input } from "@components/ui/voyager/input";
import { Select } from "@components/ui/voyager/select";
import { Textarea } from "@components/ui/voyager/textarea";

const LABEL = "text-sm font-medium text-neutral-700 dark:text-neutral-300";
const CARD =
  "rounded-2xl border border-neutral-200 p-6 sm:p-8 dark:border-neutral-700";

const PROPERTY_TYPES = ["Industrial", "Flex", "Retail", "Office", "Land", "Medical"];

/**
 * "List your property" form, adapted from Voyager's add-listing flow into a
 * single focused page. No create-listing backend yet, so it submits locally
 * (shows a confirmation) — presentation only.
 */
export const ListPropertyForm = () => {
  const [submitted, setSubmitted] = useState(false);

  if (submitted) {
    return (
      <div className={`${CARD} text-center`}>
        <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          Thanks — your listing was submitted.
        </h2>
        <p className="mt-2 text-neutral-600 dark:text-neutral-300">
          Our team will review the details and follow up shortly.
        </p>
      </div>
    );
  }

  return (
    <form
      className="space-y-8"
      onSubmit={(e) => {
        e.preventDefault();
        setSubmitted(true);
      }}
    >
      {/* Property details */}
      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Property details
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Property type</span>
            <Select className="mt-1.5" defaultValue="Industrial" required>
              {PROPERTY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </label>
          <label className="block">
            <span className={LABEL}>Listing type</span>
            <Select className="mt-1.5" defaultValue="Lease" required>
              <option value="Lease">For lease</option>
              <option value="Sale">For sale</option>
            </Select>
          </label>
          <label className="block sm:col-span-2">
            <span className={LABEL}>Listing title</span>
            <Input className="mt-1.5" placeholder="Prime distribution center" required />
          </label>
          <label className="block sm:col-span-2">
            <span className={LABEL}>Description</span>
            <Textarea className="mt-1.5" rows={5} placeholder="Describe the property…" />
          </label>
        </div>
      </section>

      {/* Location */}
      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Location
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block sm:col-span-2">
            <span className={LABEL}>Street address</span>
            <Input className="mt-1.5" autoComplete="street-address" />
          </label>
          <label className="block">
            <span className={LABEL}>City</span>
            <Input className="mt-1.5" autoComplete="address-level2" required />
          </label>
          <label className="block">
            <span className={LABEL}>State</span>
            <Input className="mt-1.5" autoComplete="address-level1" required />
          </label>
        </div>
      </section>

      {/* Specs & pricing */}
      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Specs &amp; pricing
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Size (SF)</span>
            <Input className="mt-1.5" type="number" inputMode="numeric" min={0} required />
          </label>
          <label className="block">
            <span className={LABEL}>Price / rent (USD)</span>
            <Input className="mt-1.5" type="number" inputMode="numeric" min={0} />
          </label>
          <label className="block">
            <span className={LABEL}>Clear height (ft)</span>
            <Input className="mt-1.5" type="number" inputMode="numeric" min={0} />
          </label>
          <label className="block">
            <span className={LABEL}>Loading docks</span>
            <Input className="mt-1.5" type="number" inputMode="numeric" min={0} />
          </label>
        </div>
      </section>

      {/* Contact */}
      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Listing contact
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Name</span>
            <Input className="mt-1.5" autoComplete="name" required />
          </label>
          <label className="block">
            <span className={LABEL}>Email</span>
            <Input className="mt-1.5" type="email" autoComplete="email" required />
          </label>
        </div>
      </section>

      <div>
        <ButtonPrimary type="submit">Submit listing</ButtonPrimary>
      </div>
    </form>
  );
};
