import type { Case, CaseEpisode } from "../types";
import { isBeingWritten, nextEvening, opensLater } from "./caseBoard";

/** What the case file offers tonight. One place decides it, so every screen agrees. */
export type Tonight =
  | { kind: "writing" }
  | { kind: "read"; evening: CaseEpisode }
  | { kind: "waits"; evening: CaseEpisode; opensAt: string }
  | { kind: "accuse" }
  | { kind: "solved" }
  | { kind: "failed" };

export function tonight(current: Case, now: Date): Tonight {
  if (current.status === "failed") return { kind: "failed" };
  if (current.status === "solved") return { kind: "solved" };
  if (current.status === "accusing") return { kind: "accuse" };
  if (isBeingWritten(current)) return { kind: "writing" };
  const evening = nextEvening(current.episodes);
  if (!evening || evening.status === "failed") return { kind: "failed" };
  if (evening.status === "locked") return { kind: "writing" };
  if (opensLater(evening, now) && evening.available_at) {
    return { kind: "waits", evening, opensAt: evening.available_at };
  }
  return { kind: "read", evening };
}
