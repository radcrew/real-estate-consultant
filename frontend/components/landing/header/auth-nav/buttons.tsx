import Link from "next/link";

import { ButtonPrimary } from "@components/ui/voyager/button-primary";

/**
 * Logged-out header actions, styled to match the Voyager header: a plain
 * "Sign In" text link plus an indigo "Get Started" pill. Routes are unchanged.
 */
export const NavAuthButtons = () => (
  <>
    <Link
      href="/sign-in"
      className="hidden text-sm font-medium text-neutral-700 transition-colors hover:text-neutral-900 sm:inline dark:text-neutral-300 dark:hover:text-neutral-100"
    >
      Sign In
    </Link>
    <ButtonPrimary
      href="/sign-up"
      sizeClass="px-4 py-2.5"
      fontSize="text-sm font-medium"
    >
      Get Started
    </ButtonPrimary>
  </>
);
