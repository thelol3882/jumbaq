import { describe, expect, it } from "vitest";
import { formatDay, formatOpening } from "./dates";

describe("dates", () => {
  it("puts the month first", () => {
    expect(formatDay("2026-11-14T20:30:00Z", "UTC")).toBe("November 14, 2026");
  });

  it("says when an evening opens on a 12-hour clock", () => {
    expect(formatOpening("2026-11-14T20:30:00Z", "UTC")).toBe("Saturday 8:30 PM");
    expect(formatOpening("2026-11-15T09:05:00Z", "UTC")).toBe("Sunday 9:05 AM");
  });
});
