import type { Case, CaseEpisode, Clue } from "../types";

export type SuspectMark = "cleared" | "suspect";

/** Cleared once a played clue rules the suspect out. The culprit is never ruled out. */
export function suspectMark(suspectId: string, clues: readonly Clue[]): SuspectMark {
  return clues.some((c) => c.suspect_id === suspectId && c.rules_out) ? "cleared" : "suspect";
}

/** The clue that cleared the suspect, for the note next to the name. */
export function clearingClue(suspectId: string, clues: readonly Clue[]): Clue | undefined {
  return clues.find((c) => c.suspect_id === suspectId && c.rules_out);
}

export function playedCount(episodes: readonly CaseEpisode[]): number {
  return episodes.filter((e) => e.status === "played").length;
}

/** The evening to play next: the first one not played yet, or none when all are played. */
export function nextEvening(episodes: readonly CaseEpisode[]): CaseEpisode | undefined {
  return episodes.find((e) => e.status !== "played");
}

/** True while the worker is still writing something this screen waits for. */
export function isBeingWritten(current: Case): boolean {
  if (current.status === "planning") return true;
  const next = nextEvening(current.episodes);
  return current.status === "active" && (next?.status === "requested" || next?.status === "generating");
}

/** True when the evening exists but its time has not come yet. */
export function opensLater(episode: CaseEpisode, now: Date): boolean {
  return episode.available_at !== null && new Date(episode.available_at) > now;
}
