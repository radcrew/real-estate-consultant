import { Menu as MenuPrimitive } from "@base-ui/react/menu";

import { cn } from "@lib/utils";

import {
  DROPDOWN_MENU_CONTENT_POPUP,
  DROPDOWN_MENU_POSITIONER,
} from "./styles";

export function DropdownMenuContent({
  align = "start",
  alignOffset = 0,
  side = "bottom",
  sideOffset = 4,
  className,
  ...props
}: MenuPrimitive.Popup.Props &
  Pick<
    MenuPrimitive.Positioner.Props,
    "align" | "alignOffset" | "side" | "sideOffset"
  >) {
  return (
    <MenuPrimitive.Portal>
      <MenuPrimitive.Positioner
        className={DROPDOWN_MENU_POSITIONER}
        align={align}
        alignOffset={alignOffset}
        side={side}
        sideOffset={sideOffset}
      >
        <MenuPrimitive.Popup
          data-slot="dropdown-menu-content"
          className={cn(DROPDOWN_MENU_CONTENT_POPUP, className)}
          {...props}
        />
      </MenuPrimitive.Positioner>
    </MenuPrimitive.Portal>
  );
}
