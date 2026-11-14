import { describe, expect, it } from "vitest";
import type { Case, CaseEpisode } from "../types";
import { caseProgress } from "./progress";

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

describe("caseProgress", () => {
  it("says case 1 is being written before it is opened", () => {
    expect(caseProgress(undefined, now)).toEqual({ kind: "writing", number: 1 });
  });

  it("names the evening to play next", () => {
    const active = caseWith("active", five([slot(1, "played"), slot(2, "played"), slot(3, "ready", "2026-11-14T17:00:00Z")]));
    expect(caseProgress(active, now)).toEqual({ kind: "evening", number: 1, evening: 3, total: 5 });
  });

  it("names the evening that opens later", () => {
    const later = caseWith("active", five([slot(1, "played"), slot(2, "ready", "2026-11-15T10:00:00Z")]));
    expect(caseProgress(later, now)).toMatchObject({ kind: "evening", evening: 2 });
  });

  it("follows the status of the case", () => {
    expect(caseProgress(caseWith("planning"), now)).toEqual({ kind: "writing", number: 1 });
    expect(caseProgress(caseWith("accusing"), now)).toEqual({ kind: "accuse", number: 1 });
    expect(caseProgress(caseWith("solved"), now)).toEqual({ kind: "solved", number: 1 });
    expect(caseProgress(caseWith("failed"), now)).toEqual({ kind: "failed", number: 1 });
  });
});
