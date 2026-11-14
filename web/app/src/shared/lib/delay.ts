/** The longest delay setTimeout takes (a 32-bit signed count of milliseconds, about 24.8 days). */
export const MAX_TIMEOUT_MS = 2 ** 31 - 1;

/** A moment after the time, so the server has certainly passed it too. */
const SLACK_MS = 1000;

/** Milliseconds to wait for an ISO time, capped for setTimeout; null when there is none or it has passed. */
export function delayUntil(iso: string | null, now: number): number | null {
  if (!iso) return null;
  const at = Date.parse(iso);
  if (Number.isNaN(at) || at <= now) return null;
  return Math.min(at - now + SLACK_MS, MAX_TIMEOUT_MS);
}
