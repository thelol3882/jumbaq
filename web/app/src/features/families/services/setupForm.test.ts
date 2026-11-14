import { describe, expect, it } from "vitest";
import {
  emptyDraft,
  hasErrors,
  nextKidKey,
  toFamilyCreate,
  toggleLabel,
  validateSetup,
  type SetupDraft,
} from "./setupForm";

const draft = (changes: Partial<SetupDraft> = {}): SetupDraft => ({
  kids: [
    { key: "a", nickname: "Aru", age: "7" },
    { key: "b", nickname: "Timur", age: "9" },
  ],
  rooms: ["kitchen"],
  objects: ["clock", "sofa", "kettle"],
  ...changes,
});

describe("validateSetup", () => {
  it("accepts a full setup", () => {
    expect(hasErrors(validateSetup(draft()))).toBe(false);
  });

  it("starts empty and asks for everything", () => {
    const errors = validateSetup(emptyDraft());
    expect(errors).toEqual({
      kid: { "kid-0": "nicknameMissing" },
      rooms: "missing",
      objects: "tooFew",
    });
  });

  it("checks each kid", () => {
    const kids = [
      { key: "a", nickname: "  ", age: "7" },
      { key: "b", nickname: "Timur", age: "2" },
      { key: "c", nickname: "Dana", age: "seven" },
      { key: "d", nickname: "x".repeat(41), age: "5" },
    ];
    expect(validateSetup(draft({ kids })).kid).toEqual({
      a: "nicknameMissing",
      b: "ageInvalid",
      c: "ageInvalid",
      d: "nicknameTooLong",
    });
  });

  it("finds nicknames that repeat in another case", () => {
    const kids = [
      { key: "a", nickname: "Aru", age: "7" },
      { key: "b", nickname: " aru ", age: "9" },
    ];
    expect(validateSetup(draft({ kids })).kids).toBe("repeated");
  });
});

describe("toFamilyCreate", () => {
  it("trims the nicknames and sends the ages as numbers", () => {
    const kids = [{ key: "a", nickname: " Aru ", age: "7" }];
    expect(toFamilyCreate(draft({ kids }))).toEqual({
      kids: [{ nickname: "Aru", age: 7 }],
      rooms: ["kitchen"],
      objects: ["clock", "sofa", "kettle"],
    });
  });
});

describe("toggleLabel", () => {
  it("adds a clean label and takes it away again", () => {
    const added = toggleLabel(["sofa"], "  Wall   clock ");
    expect(added).toEqual(["sofa", "Wall clock"]);
    expect(toggleLabel(added, "wall clock")).toEqual(["sofa"]);
  });

  it("ignores an empty label", () => {
    expect(toggleLabel(["sofa"], "   ")).toEqual(["sofa"]);
  });
});

describe("nextKidKey", () => {
  it("counts past the highest key, also after a kid was removed", () => {
    const kid = (key: string) => ({ key, nickname: "", age: "" });
    expect(nextKidKey([kid("kid-0"), kid("kid-2")])).toBe("kid-3");
    expect(nextKidKey([])).toBe("kid-0");
  });
});
