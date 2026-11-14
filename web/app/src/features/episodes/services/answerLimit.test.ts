import { describe, expect, it } from "vitest";
import { charactersLeft, MAX_ANSWER } from "./answerLimit";

describe("charactersLeft", () => {
  it("says nothing while the answer is short", () => {
    expect(charactersLeft(0)).toBeNull();
    expect(charactersLeft(MAX_ANSWER - 11)).toBeNull();
  });

  it("starts counting 10 characters before the limit", () => {
    expect(charactersLeft(MAX_ANSWER - 10)).toBe(10);
    expect(charactersLeft(MAX_ANSWER - 1)).toBe(1);
  });

  it("says none left at the limit and never goes below zero", () => {
    expect(charactersLeft(MAX_ANSWER)).toBe(0);
    expect(charactersLeft(MAX_ANSWER + 5)).toBe(0);
  });

  it("takes another limit", () => {
    expect(charactersLeft(5, 12)).toBe(7);
  });
});
