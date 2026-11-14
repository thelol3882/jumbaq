import { describe, expect, it } from "vitest";
import { numberCodeTable, shiftTable } from "./cipher";

describe("numberCodeTable", () => {
  it("starts at 1 for key 1", () => {
    const table = numberCodeTable(1);
    expect(table).toHaveLength(26);
    expect(table[0]).toEqual({ letter: "A", number: 1 });
    expect(table[25]).toEqual({ letter: "Z", number: 26 });
  });

  it("starts again at 1 for key 10", () => {
    expect(numberCodeTable(10)[0].number).toBe(1);
  });

  it("starts at 9 for key 9", () => {
    expect(numberCodeTable(9)[1]).toEqual({ letter: "B", number: 10 });
  });
});

describe("shiftTable", () => {
  it("reads coded D as plain A for key 3", () => {
    expect(shiftTable(3)[0]).toEqual({ plain: "A", coded: "D" });
  });

  it("wraps around the alphabet", () => {
    expect(shiftTable(3)[25]).toEqual({ plain: "Z", coded: "C" });
  });

  it("shifts by one for key 26", () => {
    expect(shiftTable(26)[0]).toEqual({ plain: "A", coded: "B" });
  });

  it("uses every letter once as coded", () => {
    expect(new Set(shiftTable(7).map((r) => r.coded)).size).toBe(26);
  });
});
