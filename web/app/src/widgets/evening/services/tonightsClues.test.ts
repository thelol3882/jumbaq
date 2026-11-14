import { describe, expect, it } from "vitest";
import type { EpisodeResult } from "@/features/episodes";
import { withTonightsClue } from "./tonightsClues";

const first = { episode: 1, text: "A feather.", suspect_id: "s1", rules_out: true };
const result: EpisodeResult = {
  answer: "a clock",
  resolution: "It was a clock.",
  case_clue: "A crumb.",
  cliffhanger: "Who was it?",
  decoded_word: null,
  revealed_suspect: false,
  struck_suspect_id: "s2",
  rules_out: true,
};

describe("withTonightsClue", () => {
  it("adds tonight's clue when the case does not have it yet", () => {
    expect(withTonightsClue([first], 2, result)).toEqual([
      first,
      { episode: 2, text: "A crumb.", suspect_id: "s2", rules_out: true },
    ]);
  });

  it("keeps a clue that does not rule the suspect out", () => {
    expect(withTonightsClue([], 2, { ...result, rules_out: false })).toEqual([
      { episode: 2, text: "A crumb.", suspect_id: "s2", rules_out: false },
    ]);
  });

  it("does not add it twice when the case has it", () => {
    const clues = [first, { episode: 2, text: "A crumb.", suspect_id: "s2", rules_out: true }];
    expect(withTonightsClue(clues, 2, result)).toEqual(clues);
  });

  it("does nothing when it is not known whether the clue rules the suspect out", () => {
    expect(withTonightsClue([first], 2, { ...result, rules_out: null })).toEqual([first]);
  });

  it("does nothing without a struck suspect or a result", () => {
    expect(withTonightsClue([first], 2, { ...result, struck_suspect_id: null })).toEqual([first]);
    expect(withTonightsClue([first], 2, undefined)).toEqual([first]);
  });
});
