import { Menu as MenuPrimitive } from "@base-ui/react/menu";

import { cn } from "@lib/utils";

import { DROPDOWN_MENU_SEPARATOR } from "./styles";

export function DropdownMenuSeparator({
  className,
  ...props
}: MenuPrimitive.Separator.Props) {
  return (
    <MenuPrimitive.Separator
      data-slot="dropdown-menu-separator"
      className={cn(DROPDOWN_MENU_SEPARATOR, className)}
      {...props}
    />
  );
}
