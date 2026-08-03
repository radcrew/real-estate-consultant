/**
 * Horizontal shell shared by every page's main content, so a spacing change
 * happens in one place instead of ~15 hand-repeated `mx-auto max-w-screen-xl
 * px-4` strings.
 *
 * The site header is not one of them — it spans the full viewport so the logo
 * sits near the edge rather than ~200px inside it on wide screens.
 *
 * Vertical rhythm stays with each page — only the width and side padding are
 * shared. Compose with `cn(PAGE_CONTAINER, "py-16 lg:py-20")`.
 */
export const PAGE_CONTAINER = "mx-auto w-full max-w-screen-2xl px-3 2xl:px-8";
