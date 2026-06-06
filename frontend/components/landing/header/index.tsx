import { Logo } from "@components/ui/voyager/logo";
import { MenuBar } from "@components/ui/voyager/menu-bar";
import { Navigation } from "@components/ui/voyager/navigation";
import { SwitchDarkMode } from "@components/ui/voyager/switch-dark-mode";

import { AuthNav } from "./auth-nav";

/**
 * Site header in Voyager's MainNav layout (h-20 bar: logo + desktop nav on the
 * left; theme toggle + auth on the right, with a mobile menu under lg). The
 * existing auth-aware `AuthNav` is kept intact so sign-in / profile behaviour is
 * unchanged.
 */
export const Header = () => (
  <header className="sticky top-0 right-0 left-0 z-40 w-full border-b border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900">
    <div className="relative mx-auto flex h-20 max-w-screen-xl items-center justify-between px-4">
      <div className="flex flex-1 items-center justify-start space-x-4 sm:space-x-10">
        <Logo className="shrink-0 self-center" />
        <Navigation />
      </div>

      <div className="flex shrink-0 items-center justify-end text-neutral-700 dark:text-neutral-100">
        <div className="hidden items-center gap-3 sm:gap-4 lg:flex">
          <SwitchDarkMode />
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
