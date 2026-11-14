type Clue = { episode: number; text: string; suspect_id: string; rules_out: boolean };

type Result = { case_clue: string; struck_suspect_id: string | null; rules_out: boolean | null };

/** The case gets tonight's clue only after the worker ran, so the evening adds it itself to cross the suspect out at once. */
export function withTonightsClue<T extends Clue>(clues: readonly T[], number: number, result: Result | null | undefined): readonly Clue[] {
  if (!result || result.struck_suspect_id === null || result.rules_out === null) return clues;
  if (clues.some((c) => c.episode === number)) return clues;
  return [...clues, { episode: number, text: result.case_clue, suspect_id: result.struck_suspect_id, rules_out: result.rules_out }];
}
