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
  "pillow",
  "shoes",
  "teddyBear",
  "spoon",
  "towel",
  "rug",
] as const;

// What a new setup starts with: the parent unticks instead of typing. "kettle" stays offered
// but not ticked. "window" is not offered at all: the backend episode check bans the word.
export const DEFAULT_ROOMS = ["kitchen", "livingRoom", "kidsRoom"] as const satisfies readonly (typeof ROOM_PRESETS)[number][];

export const DEFAULT_OBJECTS = [
  "clock",
  "sofa",
  "lamp",
  "pillow",
  "shoes",
  "spoon",
  "towel",
  "rug",
  "teddyBear",
] as const satisfies readonly (typeof OBJECT_PRESETS)[number][];

// Detective nicknames to tap, texts in locales/en.json under kids.presets.*. Kid N starts with preset N.
export const NICKNAME_PRESETS = ["fox", "owl", "eagleEye", "ace", "scout", "shadow", "comet", "pepper"] as const;

// How many detectives the setup offers; the backend takes more (MAX_KIDS) but a phone offers three.
export const KID_COUNTS = [1, 2, 3] as const;

export type RoomPreset = (typeof ROOM_PRESETS)[number];
export type ObjectPreset = (typeof OBJECT_PRESETS)[number];
