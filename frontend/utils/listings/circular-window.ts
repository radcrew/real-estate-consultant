/** Up to ``count`` consecutive images starting at ``start``, wrapping at the end of ``urls``. */
export function circularWindow(urls: string[], start: number, count: number): string[] {
  const n = urls.length;
  if (n === 0) {
    return [];
  }
  const w = Math.min(Math.max(count, 1), n);
  return Array.from({ length: w }, (_, i) => urls[(start + i) % n]!);
}
