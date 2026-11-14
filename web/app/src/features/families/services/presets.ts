// The rooms and objects offered in the setup. Their texts are in locales/en.json under
// rooms.* and objects.*; what the parent picks is sent as that text.
export const ROOM_PRESETS = ["kitchen", "livingRoom", "bedroom", "kidsRoom", "bathroom", "hallway"] as const;

export const OBJECT_PRESETS = [
  "clock",
  "fridge",
  "sofa",
  "bookshelf",
  "kettle",
  "mirror",
  "plant",
  "lamp",
  "tv",
  "window",
  "pillow",
  "shoes",
  "teddyBear",
  "spoon",
  "towel",
  "rug",
] as const;

export type RoomPreset = (typeof ROOM_PRESETS)[number];
export type ObjectPreset = (typeof OBJECT_PRESETS)[number];
