// The same limit as the backend: the answer goes into the story read aloud.
export const MAX_ANSWER = 60;

/** From how many characters left the counter shows. */
export const WARN_WITHIN = 10;

/** How many characters are left, or null while the answer is far from the limit. */
export function charactersLeft(length: number, max: number = MAX_ANSWER): number | null {
  const left = Math.max(0, max - length);
  return left <= WARN_WITHIN ? left : null;
}
