import { ButtonSecondary } from "@components/ui/voyager/button-secondary";
import { Logo } from "@components/ui/voyager/logo";
import { MenuBar } from "@components/ui/voyager/menu-bar";
import { Navigation } from "@components/ui/voyager/navigation";
import { SwitchDarkMode } from "@components/ui/voyager/switch-dark-mode";

import { AuthNav } from "./auth-nav";
import { SearchDropdown } from "./search-dropdown";

/**
 * Site header in Voyager's MainNav layout (h-20 bar: logo + desktop nav on the
 * left; theme toggle + auth on the right, with a mobile menu under lg). The
 * existing auth-aware `AuthNav` is kept intact so sign-in / profile behaviour is
 * unchanged.
 */
export const Header = () => (
  <header className="sticky top-0 right-0 left-0 z-40 w-full border-b border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900">
    <div className="relative mx-auto flex h-20 max-w-screen-xl items-center justify-between px-4 2xl:max-w-screen-2xl 2xl:px-32">
      <div className="flex flex-1 items-center justify-start space-x-4 sm:space-x-10">
        <Logo className="shrink-0 self-center" />
        <Navigation />
      </div>

      <div className="flex shrink-0 items-center justify-end text-neutral-700 dark:text-neutral-100">
        <div className="hidden items-center gap-2 lg:flex">
          <SearchDropdown />
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
