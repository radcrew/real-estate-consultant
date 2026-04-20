import { Menu as MenuPrimitive } from "@base-ui/react/menu";
import { CheckIcon } from "lucide-react";

import { cn } from "@lib/utils";

import {
  DROPDOWN_MENU_CHECKABLE_ITEM,
  DROPDOWN_MENU_ITEM_INDICATOR_WRAPPER,
} from "./styles";

export function DropdownMenuCheckboxItem({
  className,
  children,
  checked,
  inset,
  ...props
}: MenuPrimitive.CheckboxItem.Props & {
  inset?: boolean;
}) {
  return (
    <MenuPrimitive.CheckboxItem
      data-slot="dropdown-menu-checkbox-item"
      data-inset={inset}
      className={cn(DROPDOWN_MENU_CHECKABLE_ITEM, className)}
      checked={checked}
      {...props}
    >
      <span
        className={DROPDOWN_MENU_ITEM_INDICATOR_WRAPPER}
        data-slot="dropdown-menu-checkbox-item-indicator"
      >
        <MenuPrimitive.CheckboxItemIndicator>
          <CheckIcon />
        </MenuPrimitive.CheckboxItemIndicator>
      </span>
      {children}
    </MenuPrimitive.CheckboxItem>
  );
}
