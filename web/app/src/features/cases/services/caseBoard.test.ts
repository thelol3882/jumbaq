import { describe, expect, it } from "vitest";
import type { Case, CaseEpisode, Clue } from "../types";
import { isBeingWritten, nextEvening, opensLater, playedCount, suspectMark } from "./caseBoard";

const clue = (episode: number, suspect_id: string, rules_out: boolean): Clue => ({
  episode,
  suspect_id,
  rules_out,
  text: `clue ${episode}`,
});

const slot = (number: number, status: CaseEpisode["status"], available_at: string | null = null): CaseEpisode => ({
  number,
  status,
  available_at,
  id: status === "locked" ? null : `00000000-0000-0000-0000-00000000000${number}`,
});

const caseWith = (status: Case["status"], episodes: CaseEpisode[]): Case => ({
  id: "c",
  number: 1,
  status,
  title: "The Missing Midnight Cookie",
  suspects: [],
  clues: [],
  episodes,
  accusation_attempts: 0,
  rank: null,
});

describe("suspects", () => {
  it("are cleared only by a clue that rules them out", () => {
    const clues = [clue(1, "bram", true), clue(2, "pickle", false)];
    expect(suspectMark("bram", clues)).toBe("cleared");
    expect(suspectMark("pickle", clues)).not.toBe("cleared");
    expect(suspectMark("tess", clues)).toBe("suspect");
  });

  it("are pointed at by a clue that does not rule them out", () => {
    const clues = [clue(1, "pickle", false), clue(2, "bram", false), clue(3, "bram", true)];
    expect(suspectMark("pickle", clues)).toBe("pointed");
    expect(suspectMark("bram", clues)).toBe("cleared");
    expect(suspectMark("tess", clues)).toBe("suspect");
  });
});

describe("evenings", () => {
  const episodes = [slot(1, "played"), slot(2, "ready"), slot(3, "locked"), slot(4, "locked"), slot(5, "locked")];

  it("count the played ones and find the next", () => {
    expect(playedCount(episodes)).toBe(1);
    expect(nextEvening(episodes)?.number).toBe(2);
    expect(nextEvening(episodes.map((e) => ({ ...e, status: "played" as const })))).toBeUndefined();
  });

  it("know when the worker is still writing", () => {
    expect(isBeingWritten(caseWith("planning", []))).toBe(true);
    expect(isBeingWritten(caseWith("active", episodes))).toBe(false);
    expect(isBeingWritten(caseWith("active", [slot(1, "generating")]))).toBe(true);
    // Planned, but evening 1 is not requested yet: it comes with the next event.
    expect(isBeingWritten(caseWith("active", [slot(1, "locked"), slot(2, "locked")]))).toBe(true);
    // Every evening played: the case moves to the accusation with the next event.
    expect(isBeingWritten(caseWith("active", [slot(1, "played"), slot(2, "played")]))).toBe(true);
    expect(isBeingWritten(caseWith("solved", [slot(1, "generating")]))).toBe(false);
  });

  it("know when an evening opens later", () => {
    const now = new Date("2026-11-14T12:00:00Z");
    expect(opensLater(slot(3, "ready", "2026-11-15T04:00:00Z"), now)).toBe(true);
    expect(opensLater(slot(2, "ready", "2026-11-14T11:00:00Z"), now)).toBe(false);
    expect(opensLater(slot(3, "locked"), now)).toBe(false);
  });
});
