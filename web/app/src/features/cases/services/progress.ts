import type { Case } from "../types";
import { tonight } from "./tonight";

/** Where the family stands in its case, for one line of text. */
export type CaseProgress =
  | { kind: "evening"; number: number; evening: number; total: number }
  | { kind: "writing"; number: number }
  | { kind: "accuse"; number: number }
  | { kind: "solved"; number: number }
  | { kind: "failed"; number: number };

/** `undefined` is a case that is not opened yet: case 1 right after the setup. */
export function caseProgress(current: Case | undefined, now: Date): CaseProgress {
  if (!current) return { kind: "writing", number: 1 };
  const number = current.number;
  const step = tonight(current, now);
  switch (step.kind) {
    case "read":
    case "waits":
      return { kind: "evening", number, evening: step.evening.number, total: current.episodes.length };
    default:
      return { kind: step.kind, number };
  }
}
