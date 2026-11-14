const DAY = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "long", year: "numeric" });
const TIME = new Intl.DateTimeFormat("en-GB", { weekday: "long", hour: "2-digit", minute: "2-digit" });

/** "14 November 2026", in the zone of the device: the family reads it at home. */
export function formatDay(iso: string): string {
  return DAY.format(new Date(iso));
}

/** "Saturday 08:30", for when the next evening opens. */
export function formatOpening(iso: string): string {
  return TIME.format(new Date(iso));
}
