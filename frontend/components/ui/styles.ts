/**
 * Horizontal shell shared by the site header and every page's main content, so
 * the logo stays aligned with the content edge below it and a spacing change
 * happens in one place instead of ~15 hand-repeated `mx-auto max-w-screen-xl
 * px-4` strings.
 *
 * Vertical rhythm stays with each page — only the width and side padding are
 * shared. Compose with `cn(PAGE_CONTAINER, "py-16 lg:py-20")`.
 */
export const PAGE_CONTAINER = "mx-auto w-full max-w-screen-2xl px-3 2xl:px-8";
