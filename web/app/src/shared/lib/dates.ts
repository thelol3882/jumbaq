// The parents are in the US: month first and a 12-hour clock.
const LOCALE = "en-US";

/** "November 14, 2026", in the zone of the device: the family reads it at home. */
export function formatDay(iso: string, timeZone?: string): string {
  return new Intl.DateTimeFormat(LOCALE, { day: "numeric", month: "long", year: "numeric", timeZone }).format(new Date(iso));
}

/** "Saturday 8:30 PM", for when the next evening opens. */
export function formatOpening(iso: string, timeZone?: string): string {
  return new Intl.DateTimeFormat(LOCALE, { weekday: "long", hour: "numeric", minute: "2-digit", timeZone }).format(new Date(iso));
}
