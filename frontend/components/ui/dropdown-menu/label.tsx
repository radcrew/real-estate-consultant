import { Menu as MenuPrimitive } from "@base-ui/react/menu";

import { cn } from "@lib/utils";

import { DROPDOWN_MENU_LABEL } from "./styles";

export function DropdownMenuLabel({
  className,
  inset,
  ...props
}: MenuPrimitive.GroupLabel.Props & {
  inset?: boolean;
}) {
  return (
    <MenuPrimitive.GroupLabel
      data-slot="dropdown-menu-label"
      data-inset={inset}
      className={cn(DROPDOWN_MENU_LABEL, className)}
      {...props}
    />
  );
}
