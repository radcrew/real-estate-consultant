"use client";

import { useState } from "react";

import { ButtonPrimary } from "@components/ui/button-primary";
import { Input } from "@components/ui/input";
import { Select } from "@components/ui/select";
import { Textarea } from "@components/ui/textarea";
import { listingsService } from "@services/listings";
import { getApiErrorMessage } from "@utils/common";

const LABEL = "text-sm font-medium text-neutral-700 dark:text-neutral-300";
const CARD =
  "rounded-2xl border border-neutral-200 p-6 sm:p-8 dark:border-neutral-700";

const PROPERTY_TYPES = ["Industrial", "Flex", "Retail", "Office", "Land", "Medical"];

type FormState = {
  property_type: string;
  listing_type: string;
  title: string;
  description: string;
  address: string;
  city: string;
  state: string;
  size_sqft: string;
  price: string;
  clear_height: string;
  loading_docks: string;
  contact_name: string;
  contact_email: string;
};

const INITIAL: FormState = {
  property_type: "Industrial",
  listing_type: "Lease",
  title: "",
  description: "",
  address: "",
  city: "",
  state: "",
  size_sqft: "",
  price: "",
  clear_height: "",
  loading_docks: "",
  contact_name: "",
  contact_email: "",
};

const num = (v: string): number | null => {
  const t = v.trim();
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
};

/**
 * "List your property" form, adapted from Voyager's add-listing flow. Submits to
 * the public `POST /listings/submissions` endpoint (stored as 'pending').
 */
export const ListPropertyForm = () => {
  const [form, setForm] = useState<FormState>(INITIAL);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const set = (key: keyof FormState, value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await listingsService.submitListing({
        property_type: form.property_type,
        listing_type: form.listing_type,
        title: form.title.trim(),
        description: form.description.trim() || null,
        address: form.address.trim() || null,
        city: form.city.trim(),
        state: form.state.trim(),
        size_sqft: num(form.size_sqft),
        price: num(form.price),
        clear_height: num(form.clear_height),
        loading_docks: num(form.loading_docks),
        contact_name: form.contact_name.trim(),
        contact_email: form.contact_email.trim(),
      });
      setSubmitted(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

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
    <form className="space-y-8" onSubmit={onSubmit}>
      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Property details
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Property type</span>
            <Select
              className="mt-1.5"
              value={form.property_type}
              onChange={(e) => set("property_type", e.target.value)}
            >
              {PROPERTY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </Select>
          </label>
          <label className="block">
            <span className={LABEL}>Listing type</span>
            <Select
              className="mt-1.5"
              value={form.listing_type}
              onChange={(e) => set("listing_type", e.target.value)}
            >
              <option value="Lease">For lease</option>
              <option value="Sale">For sale</option>
            </Select>
          </label>
          <label className="block sm:col-span-2">
            <span className={LABEL}>Listing title</span>
            <Input
              className="mt-1.5"
              placeholder="Prime distribution center"
              required
              value={form.title}
              onChange={(e) => set("title", e.target.value)}
            />
          </label>
          <label className="block sm:col-span-2">
            <span className={LABEL}>Description</span>
            <Textarea
              className="mt-1.5"
              rows={5}
              placeholder="Describe the property…"
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
          </label>
        </div>
      </section>

      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Location
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block sm:col-span-2">
            <span className={LABEL}>Street address</span>
            <Input
              className="mt-1.5"
              autoComplete="street-address"
              value={form.address}
              onChange={(e) => set("address", e.target.value)}
            />
          </label>
          <label className="block">
            <span className={LABEL}>City</span>
            <Input
              className="mt-1.5"
              autoComplete="address-level2"
              required
              value={form.city}
              onChange={(e) => set("city", e.target.value)}
            />
          </label>
          <label className="block">
            <span className={LABEL}>State</span>
            <Input
              className="mt-1.5"
              autoComplete="address-level1"
              required
              value={form.state}
              onChange={(e) => set("state", e.target.value)}
            />
          </label>
        </div>
      </section>

      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Specs &amp; pricing
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Size (SF)</span>
            <Input
              className="mt-1.5"
              type="number"
              inputMode="numeric"
              min={0}
              required
              value={form.size_sqft}
              onChange={(e) => set("size_sqft", e.target.value)}
            />
          </label>
          <label className="block">
            <span className={LABEL}>Price / rent (USD)</span>
            <Input
              className="mt-1.5"
              type="number"
              inputMode="numeric"
              min={0}
              value={form.price}
              onChange={(e) => set("price", e.target.value)}
            />
          </label>
          <label className="block">
            <span className={LABEL}>Clear height (ft)</span>
            <Input
              className="mt-1.5"
              type="number"
              inputMode="numeric"
              min={0}
              value={form.clear_height}
              onChange={(e) => set("clear_height", e.target.value)}
            />
          </label>
          <label className="block">
            <span className={LABEL}>Loading docks</span>
            <Input
              className="mt-1.5"
              type="number"
              inputMode="numeric"
              min={0}
              value={form.loading_docks}
              onChange={(e) => set("loading_docks", e.target.value)}
            />
          </label>
        </div>
      </section>

      <section className={CARD}>
        <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          Listing contact
        </h2>
        <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <label className="block">
            <span className={LABEL}>Name</span>
            <Input
              className="mt-1.5"
              autoComplete="name"
              required
              value={form.contact_name}
              onChange={(e) => set("contact_name", e.target.value)}
            />
          </label>
          <label className="block">
            <span className={LABEL}>Email</span>
            <Input
              className="mt-1.5"
              type="email"
              autoComplete="email"
              required
              value={form.contact_email}
              onChange={(e) => set("contact_email", e.target.value)}
            />
          </label>
        </div>
      </section>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <div>
        <ButtonPrimary type="submit" disabled={submitting} loading={submitting}>
          {submitting ? "Submitting…" : "Submit listing"}
        </ButtonPrimary>
      </div>
    </form>
  );
};
