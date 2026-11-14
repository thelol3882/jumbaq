import type { TagType } from "./baseApi";

/** Tags of a list query: one per item, plus `LIST` for creates that add to it. */
export const listTags = <T extends TagType>(type: T, items: readonly { id: string }[] = []) => [
  ...items.map(({ id }) => ({ type, id })),
  { type, id: "LIST" },
];

/** Tags of one item and the lists it is in. */
export const itemTags = <T extends TagType>(type: T, id: string) => [
  { type, id },
  { type, id: "LIST" },
];
