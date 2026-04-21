import { Menu as MenuPrimitive } from "@base-ui/react/menu";

import { cn } from "@lib/utils";

import { DROPDOWN_MENU_ITEM } from "./styles";

export function DropdownMenuItem({
  className,
  inset,
  variant = "default",
  ...props
}: MenuPrimitive.Item.Props & {
  inset?: boolean;
  variant?: "default" | "destructive";
}) {
  return (
    <MenuPrimitive.Item
      data-slot="dropdown-menu-item"
      data-inset={inset}
      data-variant={variant}
      className={cn(DROPDOWN_MENU_ITEM, className)}
      {...props}
    />
  );
}
