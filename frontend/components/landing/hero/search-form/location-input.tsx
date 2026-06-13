"use client";

import { Fragment } from "react";
import { Popover, Transition } from "@headlessui/react";
import { MapPin } from "lucide-react";

import { cn } from "@utils/common";
import { useLocation } from "../../../../hooks/use-location";

import { FIELD_FOCUSED, FIELD_PADDING } from "./styles";

type LocationInputProps = {
  value: string;
  onChange: (value: string) => void;
  className?: string;
};

export const LocationInput = ({ value, onChange, className }: LocationInputProps) => {
  const {
    query,
    suggestions,
    isLoadingSuggestions,
    loadError,
    showSuggestionList,
    placesHostRef,
    handleQueryChange,
    selectSuggestion,
  } = useLocation({
    initialQuery: value,
    onChange,
  });

  return (
    <Popover className={cn("relative flex", className)}>
      {({ open }) => (
        <>
          <Popover.Button
            className={cn(
              "z-10 flex w-full flex-shrink-0 items-center space-x-3 text-left focus:outline-none",
              FIELD_PADDING,
              open && FIELD_FOCUSED,
            )}
          >
            <div className="text-neutral-300 dark:text-neutral-400">
              <MapPin className="size-5 lg:size-7" aria-hidden />
            </div>
            <div className="flex-1">
              <span className="block overflow-hidden font-semibold xl:text-lg">
                <span className="line-clamp-1">{query || "Location"}</span>
              </span>
              <span className="mt-1 block text-sm font-light leading-none text-neutral-400">
                Where are you searching?
              </span>
            </div>
          </Popover.Button>

          {open && (
            <div className="absolute inset-x-0.5 top-1/2 z-0 h-8 -translate-y-1/2 self-center bg-white dark:bg-neutral-800" />
          )}

          <Transition
            as={Fragment}
            enter="transition ease-out duration-200"
            enterFrom="opacity-0 translate-y-1"
            enterTo="opacity-100 translate-y-0"
            leave="transition ease-in duration-150"
            leaveFrom="opacity-100 translate-y-0"
            leaveTo="opacity-0 translate-y-1"
          >
            <Popover.Panel className="absolute left-0 top-full z-20 mt-3 w-full min-w-0 rounded-3xl bg-white px-4 py-5 shadow-xl dark:bg-neutral-800 sm:min-w-[340px] sm:px-8 sm:py-6">
              <input
                type="text"
                value={query}
                onChange={(e) => handleQueryChange(e.target.value)}
                placeholder="Type a city or submarket"
                className="block w-full rounded-2xl border-neutral-200 bg-white text-sm font-normal focus:border-primary-300 focus:ring-2 focus:ring-primary-200/50 dark:border-neutral-700 dark:bg-neutral-900"
              />

              {loadError && (
                <p className="mt-2 text-xs text-neutral-400">{loadError}</p>
              )}

              {isLoadingSuggestions && (
                <p className="mt-2 text-xs text-neutral-400">Searching locations…</p>
              )}

              {showSuggestionList && (
                <div className="mt-4 flex flex-col">
                  {suggestions.map((suggestion) => (
                    <Popover.Button
                      key={suggestion.placeId}
                      type="button"
                      onClick={() => selectSuggestion(suggestion)}
                      className="flex items-center space-x-3 rounded-lg p-2 text-left hover:bg-neutral-100 dark:hover:bg-neutral-700"
                    >
                      <MapPin className="size-5 shrink-0 text-neutral-400" aria-hidden />
                      <span className="text-sm text-neutral-700 dark:text-neutral-200">
                        {suggestion.label}
                      </span>
                    </Popover.Button>
                  ))}
                </div>
              )}

              <div ref={placesHostRef} className="hidden" />
            </Popover.Panel>
          </Transition>
        </>
      )}
    </Popover>
  );
};
