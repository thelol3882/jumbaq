import type { Case } from "../types";

/**
 * The opening of a case: from the moment it is opened until evening 1 is played. The family
 * page keeps it on screen the whole time, so evening 1 being written never swaps the page
 * under the parent mid-reading.
 */
export function inOpening(current: Case | undefined): boolean {
  if (!current) return true;
  if (current.status === "planning") return true;
  if (current.status !== "active") return false;
  const first = current.episodes.find((e) => e.number === 1);
  return first !== undefined && first.status !== "played" && first.status !== "failed";
}

export type OpeningStamps = { opened: boolean; suspects: boolean; firstClue: boolean };

/** Set by real states only: the family exists, the case is planned, evening 1 is written. */
export function openingStamps(current: Case | undefined): OpeningStamps {
  const first = current?.episodes.find((e) => e.number === 1);
  return {
    opened: true,
    suspects: current !== undefined && current.status !== "planning" && current.suspects.length > 0,
    firstClue: first?.status === "ready" || first?.status === "played",
  };
}
