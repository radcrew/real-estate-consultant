/**
 * Prevents nested clear hit targets from toggling the menu trigger
 * (Base UI menu can open on pointer down).
 */
export function stopMenuTriggerBubble(e: { preventDefault: () => void; stopPropagation: () => void }): void {
  e.preventDefault();
  e.stopPropagation();
}
