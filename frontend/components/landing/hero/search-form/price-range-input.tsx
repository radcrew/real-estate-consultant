"use client";

import { Fragment } from "react";
import { Popover, Transition } from "@headlessui/react";
import { DollarSign, Search } from "lucide-react";

import { cn } from "@utils/common";

import { FIELD_FOCUSED, FIELD_PADDING } from "./styles";

const formatThousand = (value: number) => value.toLocaleString("en-US");

const PRICE_LABEL = "flex-1 text-sm font-medium text-neutral-700 dark:text-neutral-300";
const CURRENCY_PREFIX = "pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-sm text-neutral-500";
const PRICE_INPUT = "block w-full rounded-full border-neutral-200 bg-transparent pl-7 pr-3 text-sm text-neutral-900 focus:border-primary-500 focus:ring-primary-500 dark:border-neutral-500 dark:text-neutral-200";

type PriceRangeInputProps = {
  value: [number, number];
  onChange: (value: [number, number]) => void;
  submitting?: boolean;
};

export const PriceRangeInput = ({ value, onChange, submitting }: PriceRangeInputProps) => {
  const [min, max] = value;

  return (
    <Popover className="relative flex flex-[1.3]">
      {({ open }) => (
        <>
          <div className="z-10 flex flex-1 items-center focus:outline-none">
            <Popover.Button
              className={cn(
                "flex flex-1 items-center space-x-3 text-left focus:outline-none",
                FIELD_PADDING,
                open && FIELD_FOCUSED,
              )}
            >
              <div className="text-neutral-300 dark:text-neutral-400">
                <DollarSign className="size-5 lg:size-7" aria-hidden />
              </div>
              <div className="flex-grow">
                <span className="block truncate font-semibold xl:text-lg">
                  {`$${formatThousand(Math.round(min / 1000))}k ~ $${formatThousand(Math.round(max / 1000))}k`}
                </span>
                <span className="mt-1 block text-sm font-light leading-none text-neutral-400">
                  Choose price range
                </span>
              </div>
            </Popover.Button>

            <div className="pr-2 xl:pr-4">
              <button
                type="submit"
                disabled={submitting}
                className="flex size-14 items-center justify-center rounded-full bg-primary-600 text-neutral-50 transition-colors hover:bg-primary-700 focus:outline-none disabled:opacity-60"
                aria-label="Search"
              >
                <Search className="size-6" aria-hidden />
              </button>
            </div>
          </div>

          {open && (
            <div className="absolute -left-0.5 right-1 top-1/2 z-0 h-8 -translate-y-1/2 self-center bg-white dark:bg-neutral-800" />
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
            <Popover.Panel className="absolute right-0 top-full z-20 mt-3 w-full max-w-sm rounded-3xl bg-white px-4 py-5 shadow-xl dark:bg-neutral-800 sm:min-w-[340px] sm:px-8 sm:py-6">
              <div className="flex flex-col space-y-6">
                <span className="font-medium">Price range</span>
                <div className="flex justify-between space-x-3">
                  <label className={PRICE_LABEL}>
                    Min price
                    <div className="relative mt-1 rounded-md">
                      <span className={CURRENCY_PREFIX}>
                        $
                      </span>
                      <input
                        type="number"
                        min={0}
                        step={1000}
                        value={min}
                        onChange={(e) => onChange([Number(e.target.value), max])}
                        className={PRICE_INPUT}
                      />
                    </div>
                  </label>
                  <label className={PRICE_LABEL}>
                    Max price
                    <div className="relative mt-1 rounded-md">
                      <span className={CURRENCY_PREFIX}>
                        $
                      </span>
                      <input
                        type="number"
                        min={0}
                        step={1000}
                        value={max}
                        onChange={(e) => onChange([min, Number(e.target.value)])}
                        className={PRICE_INPUT}
                      />
                    </div>
                  </label>
                </div>
              </div>
            </Popover.Panel>
          </Transition>
        </>
      )}
    </Popover>
  );
};
