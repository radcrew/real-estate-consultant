import * as React from "react";

import { cn } from "@lib/utils";

import { DROPDOWN_MENU_SHORTCUT } from "./styles";

export function DropdownMenuShortcut({
  className,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="dropdown-menu-shortcut"
      className={cn(DROPDOWN_MENU_SHORTCUT, className)}
      {...props}
    />
  );
}
