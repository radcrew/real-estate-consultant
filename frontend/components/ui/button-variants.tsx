import * as React from "react"
import { Button as ButtonPrimitive } from "@base-ui/react/button"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@utils/common"

const buttonRoot = [
  "group/button inline-flex shrink-0 items-center justify-center gap-1.5",
  "cursor-pointer",
  "rounded-none border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap",
  "outline-none transition-colors select-none disabled:pointer-events-none disabled:opacity-50",
  "focus-visible:ring-2 focus-visible:ring-primary-200/60 dark:focus-visible:ring-primary-600/40",
  "aria-invalid:border-destructive aria-invalid:ring-2 aria-invalid:ring-destructive/30",
  "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
].join(" ")

export const buttonVariants = cva(buttonRoot, {
  variants: {
    variant: {
      default:
        "bg-primary-600 text-white hover:bg-primary-700 [a]:hover:bg-primary-700",
      outline:
        "border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-100 aria-expanded:bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-900 dark:text-neutral-200 dark:hover:bg-neutral-800",
      secondary:
        "bg-neutral-100 text-neutral-900 hover:bg-neutral-200 aria-expanded:bg-neutral-100 dark:bg-neutral-800 dark:text-neutral-100 dark:hover:bg-neutral-700",
      ghost:
        "border-transparent hover:bg-neutral-100 hover:text-neutral-900 aria-expanded:bg-neutral-100 aria-expanded:text-neutral-900 dark:hover:bg-neutral-800 dark:hover:text-neutral-100",
      destructive:
        "bg-destructive/10 text-destructive hover:bg-destructive/20 focus-visible:border-destructive/40 focus-visible:ring-destructive/20 dark:bg-destructive/20 dark:hover:bg-destructive/30 dark:focus-visible:ring-destructive/40",
      link: "border-transparent text-primary-600 underline-offset-4 hover:underline dark:text-primary-400",
    },
    size: {
      default:
        "h-8 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
      xs: "h-6 gap-1 rounded-none px-2 text-xs has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
      sm: "h-7 gap-1 rounded-none px-2.5 text-[0.8rem] has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
      lg: "h-9 px-2.5 has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
      icon: "size-8",
      "icon-xs": "size-6 rounded-none [&_svg:not([class*='size-'])]:size-3",
      "icon-sm": "size-7 rounded-none",
      "icon-lg": "size-9",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
})

export type ButtonProps = ButtonPrimitive.Props &
  VariantProps<typeof buttonVariants>

export const Button = React.forwardRef<HTMLElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => (
    <ButtonPrimitive
      ref={ref}
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
)
Button.displayName = "Button"
