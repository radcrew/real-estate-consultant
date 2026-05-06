import type { KeyboardEvent as ReactKeyboardEvent } from "react";

/**
 * Prevents nested clear hit targets from toggling the menu trigger
 * (Base UI menu can open on pointer down).
 */
export function stopMenuTriggerBubble(e: { preventDefault: () => void; stopPropagation: () => void }): void {
  e.preventDefault();
  e.stopPropagation();
}

/** Stops Menu composite/typeahead from swallowing keys meant for inputs inside the popup. */
export function stopMenuKeyboardCapture(e: ReactKeyboardEvent): void {
  e.stopPropagation();
}
