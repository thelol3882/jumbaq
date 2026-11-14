import { describe, expect, it } from "vitest";
import { codeBreaker } from "./codeBreaker";

describe("codeBreaker", () => {
  it("names the oldest of kids with different ages", () => {
    expect(codeBreaker([{ nickname: "Mia", age: 5 }, { nickname: "Leo", age: 8 }])).toBe("Leo");
  });

  it("names no one for a single kid", () => {
    expect(codeBreaker([{ nickname: "Mia", age: 5 }])).toBeUndefined();
  });

  it("names no one when all kids are the same age", () => {
    expect(codeBreaker([{ nickname: "Mia", age: 6 }, { nickname: "Leo", age: 6 }])).toBeUndefined();
  });

  it("names no one without kids", () => {
    expect(codeBreaker([])).toBeUndefined();
  });
});
