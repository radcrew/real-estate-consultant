"use client";

import {
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
} from "@headlessui/react";
import { ChevronDown } from "lucide-react";
import Link from "next/link";

import { ButtonClose } from "@components/ui/button-close";
import { ButtonPrimary } from "@components/ui/button-primary";
import { ButtonSecondary } from "@components/ui/button-secondary";
import { ButtonThird } from "@components/ui/button-third";
import { Logo } from "@components/ui/logo";
import type { NavItemType } from "@components/ui/nav-item";
import { DEFAULT_NAV } from "@components/ui/navigation";
import { SocialsList } from "@components/ui/socials-list";
import { SwitchDarkMode } from "@components/ui/switch-dark-mode";
import { useAuth } from "@contexts/auth";

/**
 * Voyager-styled mobile nav drawer contents.
 *
 * Ported from Voyager's `shared/Navigation/NavMobile.tsx`. Headless UI v1
 * `Disclosure.*` -> v2 `DisclosureButton`/`DisclosurePanel`; Heroicons chevron
 * -> lucide. Voyager's themeforest "Get Template" link, LangDropdown and travel
 * marketing copy are removed in favour of a RadEstate description and a real
 * sign-up CTA. Uses the local default nav menu.
 */
export interface NavMobileProps {
  data?: NavItemType[];
  onClickClose?: () => void;
}

export const NavMobile = ({
  data = DEFAULT_NAV,
  onClickClose,
}: NavMobileProps) => {
  const { session, signOut } = useAuth();

  const renderItem = (item: NavItemType) => {
    if (!item.children?.length) {
      return (
        <li key={item.id} className="text-neutral-900 dark:text-white">
          <Link
            href={item.href}
            className="flex w-full rounded-lg px-4 text-sm font-medium tracking-wide uppercase hover:bg-neutral-100 dark:hover:bg-neutral-800"
          >
            <span className="block w-full py-2.5 pr-3">{item.name}</span>
          </Link>
        </li>
      );
    }

    return (
      <Disclosure
        key={item.id}
        as="li"
        className="text-neutral-900 dark:text-white"
      >
        <div className="flex w-full items-center rounded-lg pr-2 hover:bg-neutral-100 dark:hover:bg-neutral-800">
          <Link
            href={item.href}
            className="flex-1 px-4 py-2.5 text-sm font-medium tracking-wide uppercase"
          >
            {item.name}
          </Link>
          <DisclosureButton className="p-2.5">
            <ChevronDown className="h-4 w-4 text-neutral-500" aria-hidden />
          </DisclosureButton>
        </div>
        <DisclosurePanel as="ul" className="pb-1 pl-6 text-base">
          {item.children?.map((child) => (
            <li key={child.id}>
              <Link
                href={child.href}
                className="mt-0.5 flex rounded-lg px-4 text-sm font-medium text-neutral-900 hover:bg-neutral-100 dark:text-neutral-200 dark:hover:bg-neutral-800"
              >
                <span className="block w-full py-2.5 pr-3">{child.name}</span>
              </Link>
            </li>
          ))}
        </DisclosurePanel>
      </Disclosure>
    );
  };

  return (
    <div className="h-screen w-full divide-y-2 divide-neutral-100 overflow-y-auto bg-white py-2 shadow-lg ring-1 dark:divide-neutral-800 dark:bg-neutral-900 dark:ring-neutral-700">
      <div className="relative px-5 py-6">
        <Logo />
        <div className="mt-5 flex flex-col text-sm text-neutral-700 dark:text-neutral-300">
          <span>
            AI-assisted commercial real estate search — intake, fit-based ranking,
            and broker outreach drafts.
          </span>
          <div className="mt-4 flex items-center justify-between">
            <SocialsList itemClass="flex h-9 w-9 items-center justify-center rounded-full bg-neutral-100 dark:bg-neutral-800 dark:text-neutral-300" />
            <SwitchDarkMode className="bg-neutral-100 dark:bg-neutral-800" />
          </div>
        </div>
        <span className="absolute top-2 right-2 p-1">
          <ButtonClose onClick={onClickClose} />
        </span>
      </div>

      <ul className="flex flex-col space-y-1 px-2 py-6">{data.map(renderItem)}</ul>

      <div className="space-y-3 px-5 py-6">
        <ButtonSecondary href="/list-property" onClick={onClickClose}>
          List your property
        </ButtonSecondary>

        {session ? (
          <div className="flex flex-col space-y-3">
            <ButtonPrimary href="/account" onClick={onClickClose}>
              Your account
            </ButtonPrimary>
            <ButtonThird href="/saved" onClick={onClickClose}>
              Saved properties
            </ButtonThird>
            <button
              type="button"
              onClick={() => {
                onClickClose?.();
                void signOut();
              }}
              className="py-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white"
            >
              Sign out
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <ButtonThird href="/sign-in" onClick={onClickClose}>
              Sign in
            </ButtonThird>
            <ButtonPrimary href="/sign-up" onClick={onClickClose}>
              Sign up
            </ButtonPrimary>
          </div>
        )}
      </div>
    </div>
  );
};

