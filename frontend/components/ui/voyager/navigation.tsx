import {
  NavigationItem,
  type NavItemType,
} from "@components/ui/voyager/nav-item";

/**
 * Voyager-styled desktop navigation.
 *
 * Ported from Voyager's `shared/Navigation/Navigation.tsx`. Voyager's heavy
 * `NAVIGATION_DEMO` data is replaced with a small default menu of RadEstate's
 * real routes; pass `menu` to override.
 */
export const DEFAULT_NAV: NavItemType[] = [
  { id: "home", name: "Home", href: "/" },
  { id: "listings", name: "Listings", href: "/listings" },
  { id: "insights", name: "Insights", href: "/blog" },
  { id: "about", name: "About", href: "/about" },
  { id: "contact", name: "Contact", href: "/contact" },
];

export interface NavigationProps {
  menu?: NavItemType[];
}

export const Navigation = ({ menu = DEFAULT_NAV }: NavigationProps) => (
  <ul className="relative hidden lg:flex lg:flex-wrap lg:space-x-1">
    {menu.map((item) => (
      <NavigationItem key={item.id} menuItem={item} />
    ))}
  </ul>
);

export default Navigation;
