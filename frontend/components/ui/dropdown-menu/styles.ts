const MENU_ITEM_SVG =
  "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4";

export const DROPDOWN_MENU_POSITIONER = "isolate z-50 outline-none";

export const DROPDOWN_MENU_CONTENT_POPUP = [
  "z-50 max-h-(--available-height) w-(--anchor-width) min-w-32 origin-(--transform-origin)",
  "overflow-x-hidden overflow-y-auto rounded-lg bg-popover p-1 text-popover-foreground",
  "shadow-md ring-1 ring-foreground/10 duration-100 outline-none",
  "data-[side=bottom]:slide-in-from-top-2 data-[side=inline-end]:slide-in-from-left-2",
  "data-[side=inline-start]:slide-in-from-right-2 data-[side=left]:slide-in-from-right-2",
  "data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
  "data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95",
  "data-closed:animate-out data-closed:overflow-hidden data-closed:fade-out-0 data-closed:zoom-out-95",
].join(" ");

export const DROPDOWN_MENU_SUB_CONTENT_EXTRA = "w-auto min-w-[96px] shadow-lg";

export const DROPDOWN_MENU_LABEL =
  "px-1.5 py-1 text-xs font-medium text-muted-foreground data-inset:pl-7";

export const DROPDOWN_MENU_ITEM = [
  "group/dropdown-menu-item relative flex cursor-default items-center gap-1.5 rounded-md",
  "px-1.5 py-1 text-sm outline-hidden select-none",
  "focus:bg-accent focus:text-accent-foreground not-data-[variant=destructive]:focus:**:text-accent-foreground",
  "data-inset:pl-7",
  "data-[variant=destructive]:text-destructive data-[variant=destructive]:focus:bg-destructive/10",
  "data-[variant=destructive]:focus:text-destructive dark:data-[variant=destructive]:focus:bg-destructive/20",
  "data-disabled:pointer-events-none data-disabled:opacity-50",
  MENU_ITEM_SVG,
  "data-[variant=destructive]:*:[svg]:text-destructive",
].join(" ");

export const DROPDOWN_MENU_SUB_TRIGGER = [
  "flex cursor-default items-center gap-1.5 rounded-md px-1.5 py-1 text-sm outline-hidden select-none",
  "focus:bg-accent focus:text-accent-foreground not-data-[variant=destructive]:focus:**:text-accent-foreground",
  "data-inset:pl-7",
  "data-popup-open:bg-accent data-popup-open:text-accent-foreground data-open:bg-accent data-open:text-accent-foreground",
  MENU_ITEM_SVG,
].join(" ");

export const DROPDOWN_MENU_CHECKABLE_ITEM = [
  "relative flex cursor-default items-center gap-1.5 rounded-md py-1 pr-8 pl-1.5 text-sm",
  "outline-hidden select-none focus:bg-accent focus:text-accent-foreground focus:**:text-accent-foreground",
  "data-inset:pl-7 data-disabled:pointer-events-none data-disabled:opacity-50",
  MENU_ITEM_SVG,
].join(" ");

export const DROPDOWN_MENU_ITEM_INDICATOR_WRAPPER =
  "pointer-events-none absolute right-2 flex items-center justify-center";

export const DROPDOWN_MENU_SEPARATOR = "-mx-1 my-1 h-px bg-border";

export const DROPDOWN_MENU_SHORTCUT =
  "ml-auto text-xs tracking-widest text-muted-foreground group-focus/dropdown-menu-item:text-accent-foreground";
