"use client";

import { Fragment } from "react";
import { Popover, Transition } from "@headlessui/react";
import { Building2 } from "lucide-react";

import { Checkbox } from "@components/ui/checkbox";
import { cn } from "@utils/common";

import { FIELD_FOCUSED, FIELD_PADDING } from "./styles";

export type PropertyTypeOption = {
  name: string;
  description: string;
  checked: boolean;
};

export const DEFAULT_PROPERTY_TYPES: PropertyTypeOption[] = [
  { name: "Industrial", description: "Warehouse, distribution, manufacturing", checked: true },
  { name: "Flex", description: "Combined office and warehouse space", checked: false },
  { name: "Retail", description: "Storefront, shopping center, pad sites", checked: false },
  { name: "Office", description: "Professional and corporate office space", checked: false },
];

type PropertyTypeSelectProps = {
  value: PropertyTypeOption[];
  onChange: (value: PropertyTypeOption[]) => void;
};

export const PropertyTypeSelect = ({ value, onChange }: PropertyTypeSelectProps) => {
  const label = value
    .filter((item) => item.checked)
    .map((item) => item.name)
    .join(", ");

  return (
    <Popover className="relative flex flex-1">
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
              <Building2 className="size-5 lg:size-7" aria-hidden />
            </div>
            <div className="flex-1">
              <span className="block overflow-hidden font-semibold xl:text-lg">
                <span className="line-clamp-1">{label || "Type"}</span>
              </span>
              <span className="mt-1 block text-sm font-light leading-none text-neutral-400">
                Property type
              </span>
            </div>
          </Popover.Button>

          {open && (
            <div className="absolute -inset-x-0.5 top-1/2 z-0 h-8 -translate-y-1/2 self-center bg-white dark:bg-neutral-800" />
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
            <Popover.Panel className="absolute left-0 top-full z-20 mt-3 w-full max-w-sm rounded-3xl bg-white px-4 py-5 shadow-xl dark:bg-neutral-800 sm:min-w-[340px] sm:px-8 sm:py-6">
              <div className="relative flex flex-col space-y-5">
                {value.map((item, index) => (
                  <Checkbox
                    key={item.name}
                    name={item.name}
                    label={item.name}
                    subLabel={item.description}
                    defaultChecked={item.checked}
                    onChange={(checked) =>
                      onChange(
                        value.map((opt, i) =>
                          i === index ? { ...opt, checked } : opt,
                        ),
                      )
                    }
                  />
                ))}
              </div>
            </Popover.Panel>
          </Transition>
        </>
      )}
    </Popover>
  );
};
