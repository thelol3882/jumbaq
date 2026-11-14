import { describe, expect, it } from "vitest";
import type { Case, CaseEpisode } from "../types";
import { writingStage, writingSteps } from "./writing";

const slot = (number: number, status: CaseEpisode["status"]): CaseEpisode => ({
  number,
  status,
  available_at: null,
  id: status === "locked" ? null : `id-${number}`,
});
const caseWith = (status: Case["status"], statuses: CaseEpisode["status"][]): Case => ({
  id: "c",
  number: 1,
  status,
  title: status === "planning" ? null : "t",
  suspects: [],
  clues: [],
  episodes: statuses.map((s, i) => slot(i + 1, s)),
  accusation_attempts: 0,
  rank: null,
});

describe("writingStage", () => {
  it("opens the case file before there is a case", () => {
    expect(writingStage(undefined)).toEqual({ kind: "opening" });
  });

  it("plans while the case is planned", () => {
    expect(writingStage(caseWith("planning", ["locked", "locked"]))).toEqual({ kind: "planning" });
  });

  it("writes the first evening not played yet", () => {
    expect(writingStage(caseWith("active", ["generating", "locked"]))).toEqual({ kind: "evening", number: 1 });
    expect(writingStage(caseWith("active", ["played", "requested"]))).toEqual({ kind: "evening", number: 2 });
  });

  it("gathers the evidence once every evening is played", () => {
    expect(writingStage(caseWith("active", ["played", "played"]))).toEqual({ kind: "closing" });
  });
});

describe("writingSteps", () => {
  const states = (steps: ReturnType<typeof writingSteps>) => steps.map((s) => `${s.key}:${s.state}`);

  it("walks a new case to its first evening", () => {
    expect(states(writingSteps({ kind: "opening" }))).toEqual(["file:now", "plan:todo", "evening:todo"]);
    expect(states(writingSteps({ kind: "planning" }))).toEqual(["file:done", "plan:now", "evening:todo"]);
    expect(states(writingSteps({ kind: "evening", number: 1 }))).toEqual(["file:done", "plan:done", "evening:now"]);
  });

  it("shows a later evening as one step", () => {
    expect(states(writingSteps({ kind: "evening", number: 3 }))).toEqual(["evening:now"]);
    expect(states(writingSteps({ kind: "closing" }))).toEqual(["evidence:now"]);
  });
});
