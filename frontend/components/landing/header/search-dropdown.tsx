"use client";

import { Fragment } from "react";
import { Popover, Transition } from "@headlessui/react";
import { Search } from "lucide-react";
import { useRouter } from "next/navigation";

/**
 * Header search styled after Voyager's `SearchDropdown` — a search icon opening
 * a popover with a single input. This app's search is the AI-guided intake, so
 * submitting routes to the questionnaire (carrying the text as a `q` seed).
 */
type SearchDropdownProps = {
  className?: string;
};

export const SearchDropdown = ({ className = "" }: SearchDropdownProps) => {
  const router = useRouter();

  return (
    <Popover className={`relative flex ${className}`}>
      {({ close }) => (
        <>
          <Popover.Button
            aria-label="Search"
            className="flex size-12 items-center justify-center self-center rounded-full text-neutral-700 hover:bg-neutral-100 focus:outline-none dark:text-neutral-300 dark:hover:bg-neutral-800"
          >
            <Search className="size-5" aria-hidden />
          </Popover.Button>

          <Transition
            as={Fragment}
            enter="transition ease-out duration-200"
            enterFrom="opacity-0 translate-y-1"
            enterTo="opacity-100 translate-y-0"
            leave="transition ease-in duration-150"
            leaveFrom="opacity-100 translate-y-0"
            leaveTo="opacity-0 translate-y-1"
          >
            <Popover.Panel className="absolute right-0 top-full z-20 mt-3 w-screen max-w-sm">
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  const query = new FormData(event.currentTarget)
                    .get("q")
                    ?.toString()
                    .trim();
                  close();
                  router.push(
                    query ? `/questionnaire?q=${encodeURIComponent(query)}` : "/questionnaire",
                  );
                }}
              >
                <input
                  autoFocus
                  name="q"
                  type="search"
                  placeholder="Describe the space you need…"
                  aria-label="Describe the space you need"
                  className="w-full rounded-full border-neutral-200 bg-white px-5 py-3 text-sm shadow-xl focus:border-primary-300 focus:ring-3 focus:ring-primary-200/50 dark:border-neutral-700 dark:bg-neutral-900"
                />
              </form>
            </Popover.Panel>
          </Transition>
        </>
      )}
    </Popover>
  );
};
