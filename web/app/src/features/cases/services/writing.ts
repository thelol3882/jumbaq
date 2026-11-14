import type { Case } from "../types";
import { nextEvening } from "./caseBoard";

export type WritingStepKey = "file" | "plan" | "evening" | "evidence";
export type WritingStepState = "done" | "now" | "todo";
export type WritingStep = { key: WritingStepKey; state: WritingStepState };

/** What the worker is writing now, read from the case alone. */
export type WritingStage =
  | { kind: "opening" }
  | { kind: "planning" }
  | { kind: "evening"; number: number }
  | { kind: "closing" };

export function writingStage(current: Case | undefined): WritingStage {
  if (!current) return { kind: "opening" };
  if (current.status === "planning") return { kind: "planning" };
  const next = nextEvening(current.episodes);
  return next ? { kind: "evening", number: next.number } : { kind: "closing" };
}

/**
 * The steps the parent sees. Only steps the API can tell apart, so a tick is never a guess.
 * A new case shows the whole way to its first evening; a later evening is one step.
 */
export function writingSteps(stage: WritingStage): WritingStep[] {
  switch (stage.kind) {
    case "opening":
      return [step("file", "now"), step("plan", "todo"), step("evening", "todo")];
    case "planning":
      return [step("file", "done"), step("plan", "now"), step("evening", "todo")];
    case "evening":
      return stage.number === 1
        ? [step("file", "done"), step("plan", "done"), step("evening", "now")]
        : [step("evening", "now")];
    case "closing":
      return [step("evidence", "now")];
  }
}

function step(key: WritingStepKey, state: WritingStepState): WritingStep {
  return { key, state };
}
