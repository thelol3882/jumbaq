import { describe, expect, it } from "vitest";
import type { Case, CaseEpisode } from "../types";
import { tonight } from "./tonight";

const now = new Date("2026-11-14T18:00:00Z");
const slot = (number: number, status: CaseEpisode["status"], available_at: string | null = null): CaseEpisode => ({
  number,
  status,
  available_at,
  id: status === "locked" ? null : `id-${number}`,
});
const five = (first: CaseEpisode[]): CaseEpisode[] =>
  [...first, ...[1, 2, 3, 4, 5].slice(first.length).map((n) => slot(n, "locked"))];
const caseWith = (status: Case["status"], episodes: CaseEpisode[] = five([])): Case => ({
  id: "c",
  number: 1,
  status,
  title: "t",
  suspects: [],
  clues: [],
  episodes,
  accusation_attempts: 0,
  rank: null,
});

describe("tonight", () => {
  it("follows the status of the case", () => {
    expect(tonight(caseWith("planning"), now).kind).toBe("writing");
    expect(tonight(caseWith("accusing"), now).kind).toBe("accuse");
    expect(tonight(caseWith("solved"), now).kind).toBe("solved");
    expect(tonight(caseWith("failed"), now).kind).toBe("failed");
  });

  it("offers the next evening once it is written and its time has come", () => {
    const ready = caseWith("active", five([slot(1, "played"), slot(2, "ready", "2026-11-14T17:00:00Z")]));
    expect(tonight(ready, now)).toMatchObject({ kind: "read", evening: { number: 2 } });
  });

  it("waits for an evening that opens later", () => {
    const later = caseWith("active", five([slot(1, "played"), slot(2, "ready", "2026-11-15T10:00:00Z")]));
    expect(tonight(later, now)).toMatchObject({ kind: "waits", opensAt: "2026-11-15T10:00:00Z" });
  });

  it("says writing while the next evening is written", () => {
    expect(tonight(caseWith("active", five([slot(1, "generating")])), now).kind).toBe("writing");
    expect(tonight(caseWith("active", five([slot(1, "played")])), now).kind).toBe("writing");
  });

  it("says failed when an evening could not be written", () => {
    expect(tonight(caseWith("active", five([slot(1, "failed")])), now).kind).toBe("failed");
  });
});
