import { describe, expect, it } from "vitest";
import { delayUntil, MAX_TIMEOUT_MS } from "./delay";

const NOW = Date.parse("2026-11-14T20:00:00Z");

describe("delayUntil", () => {
  it("waits until just after the time", () => {
    expect(delayUntil("2026-11-14T20:01:00Z", NOW)).toBe(61_000);
  });

  it("does nothing without a time or when it has passed", () => {
    expect(delayUntil(null, NOW)).toBeNull();
    expect(delayUntil("2026-11-14T19:59:00Z", NOW)).toBeNull();
    expect(delayUntil("2026-11-14T20:00:00Z", NOW)).toBeNull();
    expect(delayUntil("not a time", NOW)).toBeNull();
  });

  it("stays within what setTimeout takes", () => {
    expect(delayUntil("2027-11-14T20:00:00Z", NOW)).toBe(MAX_TIMEOUT_MS);
  });
});
