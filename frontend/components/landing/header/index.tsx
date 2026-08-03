import { ButtonSecondary } from "@components/ui/button-secondary";
import { Logo } from "@components/ui/logo";
import { MenuBar } from "@components/ui/menu-bar";
import { Navigation } from "@components/ui/navigation";
import { SwitchDarkMode } from "@components/ui/switch-dark-mode";

import { AuthNav } from "./auth-nav";

/**
 * Site header in Voyager's MainNav layout (h-20 bar: logo + desktop nav on the
 * left; theme toggle + auth on the right, with a mobile menu under lg). The
 * existing auth-aware `AuthNav` is kept intact so sign-in / profile behaviour is
 * unchanged.
 *
 * The bar deliberately opts out of `PAGE_CONTAINER`: capping it at
 * `max-w-screen-2xl` stranded the logo ~200px from the edge on wide screens,
 * far right of the full-bleed account sidebar sitting directly under it.
 */
export const Header = () => (
  <header className="sticky top-0 right-0 left-0 z-40 w-full border-b border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900">
    <div className="relative flex h-20 w-full items-center justify-between px-4 sm:px-6">
      <div className="flex flex-1 items-center justify-start space-x-4 sm:space-x-10">
        <Logo className="shrink-0 self-center" />
        <Navigation />
      </div>

      <div className="flex shrink-0 items-center justify-end text-neutral-700 dark:text-neutral-100">
        <div className="hidden items-center gap-2 lg:flex">
          <ButtonSecondary
            href="/list-property"
            sizeClass="px-4 py-2"
            fontSize="text-sm font-medium"
          >
            List your property
          </ButtonSecondary>
          <SwitchDarkMode />
          <div className="mx-1 h-6 border-l border-neutral-200 dark:border-neutral-700" />
          <AuthNav />
        </div>
        <div className="flex items-center lg:hidden">
          <SwitchDarkMode />
          <MenuBar />
        </div>
      </div>
    </div>
  </header>
);
