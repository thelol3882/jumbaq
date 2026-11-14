import { describe, expect, it } from "vitest";
import {
  emptyDraft,
  hasErrors,
  isNicknameTaken,
  nextKidKey,
  setKidCount,
  toFamilyCreate,
  toggleLabel,
  validateSetup,
  type DraftDefaults,
  type SetupDraft,
} from "./setupForm";

const defaults: DraftDefaults = {
  nicknames: ["Fox", "Owl", "Eagle Eye", "Ace"],
  rooms: ["kitchen", "living room"],
  objects: ["clock", "sofa", "lamp"],
};

const draft = (changes: Partial<SetupDraft> = {}): SetupDraft => ({
  kids: [
    { key: "a", nickname: "Aru", age: "7", custom: true },
    { key: "b", nickname: "Timur", age: "9", custom: true },
  ],
  rooms: ["kitchen"],
  objects: ["clock", "sofa", "kettle"],
  ...changes,
});

describe("validateSetup", () => {
  it("accepts a full setup", () => {
    expect(hasErrors(validateSetup(draft()))).toBe(false);
  });

  it("starts with the defaults and asks only for the age", () => {
    const errors = validateSetup(emptyDraft(defaults));
    expect(errors).toEqual({ kid: { "kid-0": "ageInvalid" } });
  });

  it("checks each kid", () => {
    const kids = [
      { key: "a", nickname: "  ", age: "7", custom: true },
      { key: "b", nickname: "Timur", age: "2", custom: true },
      { key: "c", nickname: "Dana", age: "seven", custom: true },
      { key: "d", nickname: "x".repeat(41), age: "5", custom: true },
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
      { key: "a", nickname: "Aru", age: "7", custom: true },
      { key: "b", nickname: " aru ", age: "9", custom: true },
    ];
    expect(validateSetup(draft({ kids })).kids).toBe("repeated");
  });
});

describe("toFamilyCreate", () => {
  it("trims the nicknames and sends the ages as numbers", () => {
    const kids = [{ key: "a", nickname: " Aru ", age: "7", custom: true }];
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
    const kid = (key: string) => ({ key, nickname: "", age: "", custom: false });
    expect(nextKidKey([kid("kid-0"), kid("kid-2")])).toBe("kid-3");
    expect(nextKidKey([])).toBe("kid-0");
  });
});

describe("emptyDraft", () => {
  it("picks the first nickname, the default rooms and objects, and no age", () => {
    expect(emptyDraft(defaults)).toEqual({
      kids: [{ key: "kid-0", nickname: "Fox", age: "", custom: false }],
      rooms: ["kitchen", "living room"],
      objects: ["clock", "sofa", "lamp"],
    });
  });

  it("does not share its lists with the defaults", () => {
    emptyDraft(defaults).rooms.push("attic");
    expect(defaults.rooms).toEqual(["kitchen", "living room"]);
  });
});

describe("setKidCount", () => {
  it("adds kids with the first preset nobody uses", () => {
    const grown = setKidCount(emptyDraft(defaults), 3, defaults.nicknames);
    expect(grown.kids.map((k) => [k.key, k.nickname, k.age])).toEqual([
      ["kid-0", "Fox", ""],
      ["kid-1", "Owl", ""],
      ["kid-2", "Eagle Eye", ""],
    ]);
  });

  it("skips a preset another kid typed or took", () => {
    const start = emptyDraft(defaults);
    start.kids[0] = { ...start.kids[0], nickname: "owl", custom: true };
    expect(setKidCount(start, 2, defaults.nicknames).kids[1].nickname).toBe("Fox");
  });

  it("drops the last kids and keeps the first ones as they were", () => {
    const grown = setKidCount(emptyDraft(defaults), 3, defaults.nicknames);
    grown.kids[0] = { ...grown.kids[0], age: "6" };
    const shrunk = setKidCount(grown, 1, defaults.nicknames);
    expect(shrunk.kids).toEqual([{ key: "kid-0", nickname: "Fox", age: "6", custom: false }]);
  });

  it("keeps the kids when the count is the same and never goes below one", () => {
    const one = emptyDraft(defaults);
    expect(setKidCount(one, 1, defaults.nicknames)).toEqual(one);
    expect(setKidCount(one, 0, defaults.nicknames).kids).toHaveLength(1);
  });

  it("asks for a typed name when every preset is taken", () => {
    const last = setKidCount(emptyDraft({ ...defaults, nicknames: ["Fox"] }), 2, ["Fox"]).kids[1];
    expect(last).toMatchObject({ nickname: "", custom: true });
  });
});

describe("isNicknameTaken", () => {
  it("is true only for another kid, ignoring case", () => {
    const kids = draft().kids;
    expect(isNicknameTaken(kids, "b", " aru")).toBe(true);
    expect(isNicknameTaken(kids, "a", "Aru")).toBe(false);
    expect(isNicknameTaken(kids, "a", "Fox")).toBe(false);
  });
});
