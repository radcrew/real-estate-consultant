"use client";

import { Fragment } from "react";
import { Popover, Transition } from "@headlessui/react";
import { Heart, LogOut, UserRound } from "lucide-react";
import Link from "next/link";

import { Avatar } from "@components/ui/voyager/avatar";
import { useAuth } from "@contexts/auth";

/**
 * Account menu styled after Voyager's `AvatarDropdown` — a Headless UI Popover
 * with a rounded-3xl card panel: avatar + email header, a divider, then
 * icon-and-label rows with the Voyager hover treatment. Wired to this app's
 * auth (Account, Saved, Sign out) and lucide icons.
 */
const ITEM_CLASS =
  "-m-3 flex items-center rounded-lg p-2 text-left transition duration-150 ease-in-out hover:bg-neutral-100 focus:outline-none dark:hover:bg-neutral-700";
const ICON_WRAP =
  "flex flex-shrink-0 items-center justify-center text-neutral-500 dark:text-neutral-300";

export const ProfileDropdown = () => {
  const { session, signOut } = useAuth();
  if (!session) {
    return null;
  }

  const email = session.user.email?.trim() || "Account";
  const avatarUrl = session.user.avatarUrl?.trim() || undefined;

  return (
    <Popover className="relative flex">
      {({ close }) => (
        <>
          <Popover.Button
            aria-label="Account menu"
            className="flex size-10 items-center justify-center self-center rounded-full text-neutral-700 hover:bg-neutral-100 focus:outline-none dark:text-neutral-300 dark:hover:bg-neutral-800 sm:size-12"
          >
            <Avatar
              imgUrl={avatarUrl}
              userName={email}
              sizeClass="h-8 w-8 sm:h-9 sm:w-9"
              unoptimized
              referrerPolicy="no-referrer"
            />
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
            <Popover.Panel className="absolute right-0 top-full z-20 mt-3 w-screen max-w-[260px] px-4 sm:px-0">
              <div className="overflow-hidden rounded-3xl shadow-lg ring-1 ring-black/5">
                <div className="relative grid grid-cols-1 gap-6 bg-white px-6 py-7 dark:bg-neutral-800">
                  <div className="flex items-center space-x-3">
                    <Avatar
                      imgUrl={avatarUrl}
                      userName={email}
                      sizeClass="h-12 w-12"
                      unoptimized
                      referrerPolicy="no-referrer"
                    />
                    <div className="min-w-0 flex-grow">
                      <h4 className="truncate font-semibold">{email}</h4>
                      <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
                        Signed in
                      </p>
                    </div>
                  </div>

                  <div className="w-full border-b border-neutral-200 dark:border-neutral-700" />

                  <Link href="/account" className={ITEM_CLASS} onClick={() => close()}>
                    <div className={ICON_WRAP}>
                      <UserRound className="size-6" aria-hidden />
                    </div>
                    <p className="ml-4 text-sm font-medium">Account</p>
                  </Link>

                  <Link href="/saved" className={ITEM_CLASS} onClick={() => close()}>
                    <div className={ICON_WRAP}>
                      <Heart className="size-6" aria-hidden />
                    </div>
                    <p className="ml-4 text-sm font-medium">Saved</p>
                  </Link>

                  <div className="w-full border-b border-neutral-200 dark:border-neutral-700" />

                  <button
                    type="button"
                    className={ITEM_CLASS}
                    onClick={() => {
                      close();
                      signOut();
                    }}
                  >
                    <div className={ICON_WRAP}>
                      <LogOut className="size-6" aria-hidden />
                    </div>
                    <p className="ml-4 text-sm font-medium">Sign out</p>
                  </button>
                </div>
              </div>
            </Popover.Panel>
          </Transition>
        </>
      )}
    </Popover>
  );
};
