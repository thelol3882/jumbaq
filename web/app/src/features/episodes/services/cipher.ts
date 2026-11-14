const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

export type NumberCodeRow = { letter: string; number: number };
export type ShiftRow = { coded: string; plain: string };

/** Same formula as the server: A gets a start number from the key, B the next one, and so on. */
export function numberCodeTable(key: number): NumberCodeRow[] {
  const start = ((key - 1) % 9) + 1;
  return [...LETTERS].map((letter, index) => ({ letter, number: start + index }));
}

/** Every letter of the code was moved forward by `shift`; this table moves it back. */
export function shiftTable(key: number): ShiftRow[] {
  const shift = ((key - 1) % 25) + 1;
  return [...LETTERS].map((plain, index) => ({ plain, coded: LETTERS[(index + shift) % 26] }));
}
