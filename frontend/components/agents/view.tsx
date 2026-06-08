"use client";

import { useEffect, useState } from "react";
import { Mail, Phone } from "lucide-react";

import { Avatar } from "@components/ui/avatar";
import { NoticeCard } from "@components/ui/notice-card";
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

  if (loading) {
    return (
      <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
        <p className="text-neutral-500 dark:text-neutral-400">Loading agent…</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-screen-xl px-4 py-16 lg:py-20">
        <NoticeCard>
          <p className="text-neutral-600 dark:text-neutral-300">
            {error ?? "Agent not found."}
          </p>
        </NoticeCard>
      </div>
    );
  }

  const count = data.properties.length;

  return (
    <div className="mx-auto max-w-screen-xl px-4 py-16 lg:flex lg:gap-10 lg:py-20 xl:gap-14">
      <div className="lg:w-80 lg:shrink-0">
        <div className="flex flex-col items-center space-y-6 rounded-2xl border border-neutral-200 p-6 text-center sm:p-8 lg:sticky lg:top-24 dark:border-neutral-700">
          <Avatar userName={data.name} sizeClass="h-28 w-28 text-3xl" radius="rounded-full" />
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
              {data.name}
            </h1>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">Listing broker</p>
          </div>

          {data.email || data.phone ? (
            <>
              <div className="w-14 border-b border-neutral-200 dark:border-neutral-700" />
              <div className="w-full space-y-3 text-left">
                {data.email ? (
                  <a
                    href={`mailto:${data.email}`}
                    className="flex items-center gap-3 text-sm text-neutral-600 hover:text-primary-600 dark:text-neutral-300"
                  >
                    <Mail className="size-5 shrink-0 text-neutral-400" aria-hidden />
                    <span className="truncate">{data.email}</span>
                  </a>
                ) : null}
                {data.phone ? (
                  <a
                    href={`tel:${data.phone}`}
                    className="flex items-center gap-3 text-sm text-neutral-600 hover:text-primary-600 dark:text-neutral-300"
                  >
                    <Phone className="size-5 shrink-0 text-neutral-400" aria-hidden />
                    <span className="truncate">{data.phone}</span>
                  </a>
                ) : null}
              </div>
            </>
          ) : null}
        </div>
      </div>

      <div className="mt-10 min-w-0 flex-1 lg:mt-0">
        <h2 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          {data.name}&rsquo;s listings
        </h2>
        <span className="mt-2 block text-neutral-500 dark:text-neutral-400">
          {count} {count === 1 ? "listing" : "listings"}
        </span>
        <div className="my-6 w-14 border-b border-neutral-200 dark:border-neutral-700" />

        {count > 0 ? (
          <div className={PROPERTY_GRID}>
            {data.properties.map((property, i) => (
              <PropertyCard
                key={property.id ?? i}
                data={propertyToModel(property, i)}
              />
            ))}
          </div>
        ) : (
          <NoticeCard>
            <p className="text-neutral-600 dark:text-neutral-300">
              This broker has no active listings right now.
            </p>
          </NoticeCard>
        )}
      </div>
    </div>
  );
};
