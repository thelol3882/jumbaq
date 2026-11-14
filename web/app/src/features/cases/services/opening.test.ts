import { describe, expect, it } from "vitest";
import type { Case, CaseEpisode, Suspect } from "../types";
import { inOpening, openingStamps } from "./opening";

const slot = (number: number, status: CaseEpisode["status"]): CaseEpisode => ({
  number,
  status,
  available_at: null,
  id: status === "locked" ? null : `id-${number}`,
});
const suspect: Suspect = { id: "s1", name: "Uncle Bram", description: "always near the cookie jar" };
const caseWith = (status: Case["status"], first: CaseEpisode["status"], suspects: Suspect[] = [suspect]): Case => ({
  id: "c",
  number: 1,
  status,
  title: status === "planning" ? null : "The Missing Cookie",
  suspects: status === "planning" ? [] : suspects,
  clues: [],
  episodes: [slot(1, first), slot(2, "locked")],
  accusation_attempts: 0,
  rank: null,
});

describe("inOpening", () => {
  it("lasts from the setup until evening 1 is played", () => {
    expect(inOpening(undefined)).toBe(true);
    expect(inOpening(caseWith("planning", "locked"))).toBe(true);
    expect(inOpening(caseWith("active", "generating"))).toBe(true);
    expect(inOpening(caseWith("active", "ready"))).toBe(true);
    expect(inOpening(caseWith("active", "played"))).toBe(false);
  });

  it("gives way to the failed and the later screens", () => {
    expect(inOpening(caseWith("active", "failed"))).toBe(false);
    expect(inOpening(caseWith("failed", "locked"))).toBe(false);
    expect(inOpening(caseWith("accusing", "played"))).toBe(false);
  });
});

describe("openingStamps", () => {
  it("stamps only what the API says is done", () => {
    expect(openingStamps(undefined)).toEqual({ opened: true, suspects: false, firstClue: false });
    expect(openingStamps(caseWith("planning", "locked"))).toEqual({ opened: true, suspects: false, firstClue: false });
    expect(openingStamps(caseWith("active", "generating"))).toEqual({ opened: true, suspects: true, firstClue: false });
    expect(openingStamps(caseWith("active", "ready"))).toEqual({ opened: true, suspects: true, firstClue: true });
  });

  it("waits for the suspects even on an active case without them", () => {
    expect(openingStamps(caseWith("active", "requested", [])).suspects).toBe(false);
  });
});
