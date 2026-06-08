"use client";

import { useEffect, useState } from "react";
import { Mail, Phone } from "lucide-react";

import { Avatar } from "@components/ui/voyager/avatar";
import { propertyToModel } from "@components/voyager/listing-model";
import { PropertyCard, PROPERTY_GRID } from "@components/voyager/property-card";
import { listingsService, type AgentProfileResponse } from "@services/listings";
import { getApiErrorMessage } from "@utils/common";

type AgentViewProps = {
  broker: string;
};

export const AgentView = ({ broker }: AgentViewProps) => {
  const [data, setData] = useState<AgentProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ac = new AbortController();
    setLoading(true);
    setError(null);
    void (async () => {
      try {
        const d = await listingsService.getAgent(broker, { signal: ac.signal });
        if (!ac.signal.aborted) setData(d);
      } catch (e) {
        if (!ac.signal.aborted) setError(getApiErrorMessage(e));
      } finally {
        if (!ac.signal.aborted) setLoading(false);
      }
    })();
    return () => ac.abort();
  }, [broker]);

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
      {loading ? (
        <p className="text-neutral-500 dark:text-neutral-400">Loading agent…</p>
      ) : error || !data ? (
        <div className="rounded-2xl border border-neutral-200 p-10 text-center dark:border-neutral-700">
          <p className="text-neutral-600 dark:text-neutral-300">
            {error ?? "Agent not found."}
          </p>
        </div>
      ) : (
        <>
          <header className="flex flex-col items-start gap-5 border-b border-neutral-200 pb-10 sm:flex-row sm:items-center dark:border-neutral-700">
            <Avatar userName={data.name} sizeClass="h-20 w-20 text-2xl" radius="rounded-2xl" />
            <div className="min-w-0">
              <h1 className="text-3xl font-semibold text-neutral-900 md:text-4xl dark:text-neutral-100">
                {data.name}
              </h1>
              <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm text-neutral-500 dark:text-neutral-400">
                {data.email ? (
                  <a
                    href={`mailto:${data.email}`}
                    className="inline-flex items-center gap-1.5 hover:text-primary-600"
                  >
                    <Mail className="size-4" aria-hidden />
                    {data.email}
                  </a>
                ) : null}
                {data.phone ? (
                  <a
                    href={`tel:${data.phone}`}
                    className="inline-flex items-center gap-1.5 hover:text-primary-600"
                  >
                    <Phone className="size-4" aria-hidden />
                    {data.phone}
                  </a>
                ) : null}
              </div>
            </div>
          </header>

          <h2 className="mt-10 text-xl font-semibold text-neutral-900 dark:text-neutral-100">
            {data.properties.length}{" "}
            {data.properties.length === 1 ? "listing" : "listings"}
          </h2>
          <div className={`mt-6 ${PROPERTY_GRID}`}>
            {data.properties.map((property, i) => (
              <PropertyCard
                key={property.id ?? i}
                data={propertyToModel(property, i)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
};
