"use client";

import * as React from "react";
import { Menu as MenuPrimitive } from "@base-ui/react/menu";
import { CheckIcon, ChevronRightIcon } from "lucide-react";

import { cn } from "@utils/common";

const MENU_ITEM_SVG =
  "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4";

const POSITIONER = "isolate z-50 outline-none";

const CONTENT_POPUP = [
  "z-50 max-h-(--available-height) w-(--anchor-width) min-w-32 origin-(--transform-origin)",
  "overflow-x-hidden overflow-y-auto rounded-lg bg-white p-1 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-200",
  "shadow-md ring-1 ring-neutral-900/10 duration-100 outline-none dark:ring-white/10",
  "data-[side=bottom]:slide-in-from-top-2 data-[side=inline-end]:slide-in-from-left-2",
  "data-[side=inline-start]:slide-in-from-right-2 data-[side=left]:slide-in-from-right-2",
  "data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
  "data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95",
  "data-closed:animate-out data-closed:overflow-hidden data-closed:fade-out-0 data-closed:zoom-out-95",
].join(" ");

const SUB_CONTENT_EXTRA = "w-auto min-w-[96px] shadow-lg";

const LABEL = "px-1.5 py-1 text-xs font-medium text-neutral-500 data-inset:pl-7 dark:text-neutral-400";

const ITEM = [
  "group/dropdown-menu-item relative flex cursor-default items-center gap-1.5 rounded-md",
  "px-1.5 py-1 text-sm outline-hidden select-none",
  "focus:bg-neutral-100 focus:text-neutral-900 dark:focus:bg-neutral-700 dark:focus:text-neutral-100",
  "data-inset:pl-7",
  "data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10",
  "data-[variant=destructive]:focus:text-destructive dark:data-[variant=destructive]:focus:bg-destructive/20",
  "data-disabled:pointer-events-none data-disabled:opacity-50",
  MENU_ITEM_SVG,
  "data-[variant=destructive]:*:[svg]:text-destructive",
].join(" ");

const SUB_TRIGGER = [
  "flex cursor-default items-center gap-1.5 rounded-md px-1.5 py-1 text-sm outline-hidden select-none",
  "focus:bg-neutral-100 focus:text-neutral-900 dark:focus:bg-neutral-700 dark:focus:text-neutral-100",
  "data-inset:pl-7",
  "data-popup-open:bg-neutral-100 data-popup-open:text-neutral-900 data-open:bg-neutral-100 data-open:text-neutral-900",
  "dark:data-popup-open:bg-neutral-700 dark:data-popup-open:text-neutral-100 dark:data-open:bg-neutral-700 dark:data-open:text-neutral-100",
  MENU_ITEM_SVG,
].join(" ");

const CHECKABLE_ITEM = [
  "relative flex cursor-default items-center gap-1.5 rounded-md py-1 pr-8 pl-1.5 text-sm",
  "outline-hidden select-none focus:bg-neutral-100 focus:text-neutral-900 dark:focus:bg-neutral-700 dark:focus:text-neutral-100",
  "data-inset:pl-7 data-disabled:pointer-events-none data-disabled:opacity-50",
  MENU_ITEM_SVG,
].join(" ");

const ITEM_INDICATOR_WRAPPER =
  "pointer-events-none absolute right-2 flex items-center justify-center";

const SEPARATOR = "-mx-1 my-1 h-px bg-neutral-200 dark:bg-neutral-700";

const SHORTCUT =
  "ml-auto text-xs tracking-widest text-neutral-500 group-focus/dropdown-menu-item:text-neutral-900 dark:text-neutral-400";

export function DropdownMenu({ ...props }: MenuPrimitive.Root.Props) {
  return <MenuPrimitive.Root data-slot="dropdown-menu" {...props} />;
}

export function DropdownMenuPortal({ ...props }: MenuPrimitive.Portal.Props) {
  return <MenuPrimitive.Portal data-slot="dropdown-menu-portal" {...props} />;
}

export function DropdownMenuTrigger({ ...props }: MenuPrimitive.Trigger.Props) {
  return <MenuPrimitive.Trigger data-slot="dropdown-menu-trigger" {...props} />;
}

export function DropdownMenuGroup({ ...props }: MenuPrimitive.Group.Props) {
  return <MenuPrimitive.Group data-slot="dropdown-menu-group" {...props} />;
}

export function DropdownMenuSub({ ...props }: MenuPrimitive.SubmenuRoot.Props) {
  return <MenuPrimitive.SubmenuRoot data-slot="dropdown-menu-sub" {...props} />;
}

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
        className={POSITIONER}
        align={align}
        alignOffset={alignOffset}
        side={side}
        sideOffset={sideOffset}
      >
        <MenuPrimitive.Popup
          data-slot="dropdown-menu-content"
          className={cn(CONTENT_POPUP, className)}
          {...props}
        />
      </MenuPrimitive.Positioner>
    </MenuPrimitive.Portal>
  );
}

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
      className={cn(ITEM, className)}
      {...props}
    />
  );
}

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
      className={cn(CHECKABLE_ITEM, className)}
      checked={checked}
      {...props}
    >
      <span
        className={ITEM_INDICATOR_WRAPPER}
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

export function DropdownMenuRadioGroup({ ...props }: MenuPrimitive.RadioGroup.Props) {
  return (
    <MenuPrimitive.RadioGroup data-slot="dropdown-menu-radio-group" {...props} />
  );
}

export function DropdownMenuRadioItem({
  className,
  children,
  inset,
  ...props
}: MenuPrimitive.RadioItem.Props & {
  inset?: boolean;
}) {
  return (
    <MenuPrimitive.RadioItem
      data-slot="dropdown-menu-radio-item"
      data-inset={inset}
      className={cn(CHECKABLE_ITEM, className)}
      {...props}
    >
      <span
        className={ITEM_INDICATOR_WRAPPER}
        data-slot="dropdown-menu-radio-item-indicator"
      >
        <MenuPrimitive.RadioItemIndicator>
          <CheckIcon />
        </MenuPrimitive.RadioItemIndicator>
      </span>
      {children}
    </MenuPrimitive.RadioItem>
  );
}

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
      className={cn(LABEL, className)}
      {...props}
    />
  );
}

export function DropdownMenuSeparator({
  className,
  ...props
}: MenuPrimitive.Separator.Props) {
  return (
    <MenuPrimitive.Separator
      data-slot="dropdown-menu-separator"
      className={cn(SEPARATOR, className)}
      {...props}
    />
  );
}

export function DropdownMenuShortcut({
  className,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="dropdown-menu-shortcut"
      className={cn(SHORTCUT, className)}
      {...props}
    />
  );
}

export function DropdownMenuSubTrigger({
  className,
  inset,
  children,
  ...props
}: MenuPrimitive.SubmenuTrigger.Props & {
  inset?: boolean;
}) {
  return (
    <MenuPrimitive.SubmenuTrigger
      data-slot="dropdown-menu-sub-trigger"
      data-inset={inset}
      className={cn(SUB_TRIGGER, className)}
      {...props}
    >
      {children}
      <ChevronRightIcon className="ml-auto" />
    </MenuPrimitive.SubmenuTrigger>
  );
}

export function DropdownMenuSubContent({
  align = "start",
  alignOffset = -3,
  side = "right",
  sideOffset = 0,
  className,
  ...props
}: React.ComponentProps<typeof DropdownMenuContent>) {
  return (
    <DropdownMenuContent
      data-slot="dropdown-menu-sub-content"
      className={cn(SUB_CONTENT_EXTRA, className)}
      align={align}
      alignOffset={alignOffset}
      side={side}
      sideOffset={sideOffset}
      {...props}
    />
  );
}
