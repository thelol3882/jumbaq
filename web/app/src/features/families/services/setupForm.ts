import type { FamilyCreate } from "../types";

// The same limits as backend/jumbaq/families/schemas.py, checked here first so the
// parent sees the problem before sending.
export const MAX_KIDS = 6;
export const MIN_AGE = 3;
export const MAX_AGE = 14;
export const MAX_ROOMS = 20;
export const MIN_OBJECTS = 3;
export const MAX_OBJECTS = 100;
export const MAX_NICKNAME = 40;
export const MAX_LABEL = 60;

// `custom`: the parent chose "Write my own", so the nickname is typed, not tapped.
export type KidDraft = { key: string; nickname: string; age: string; custom: boolean };

/** The localized texts a new draft starts with. Services cannot translate, so the hook passes them. */
export type DraftDefaults = {
  nicknames: readonly string[];
  rooms: readonly string[];
  objects: readonly string[];
};

export type SetupDraft = {
  kids: KidDraft[];
  rooms: string[];
  objects: string[];
};

export type KidError = "nicknameMissing" | "nicknameTooLong" | "ageInvalid";
export type SetupErrors = {
  kids?: "repeated";
  kid?: Record<string, KidError>;
  rooms?: "missing" | "tooMany";
  objects?: "tooFew" | "tooMany";
};

export function emptyDraft(defaults: DraftDefaults): SetupDraft {
  return {
    kids: [newKid("kid-0", defaults.nicknames[0] ?? "")],
    rooms: [...defaults.rooms],
    objects: [...defaults.objects],
  };
}

// The age stays empty on purpose: a parent must pick it, and validateSetup asks for it.
function newKid(key: string, nickname: string): KidDraft {
  return { key, nickname, age: "", custom: false };
}

function sameText(a: string, b: string): boolean {
  return a.trim().toLocaleLowerCase() === b.trim().toLocaleLowerCase();
}

/** Another kid already has this nickname, so it is not free to pick. */
export function isNicknameTaken(kids: KidDraft[], key: string, nickname: string): boolean {
  return kids.some((k) => k.key !== key && sameText(k.nickname, nickname));
}

/** Changes the number of kids: drops the last ones, or adds kids with the first preset nobody uses. */
export function setKidCount(draft: SetupDraft, count: number, nicknames: readonly string[]): SetupDraft {
  const target = Math.min(Math.max(count, 1), MAX_KIDS);
  if (target <= draft.kids.length) return { ...draft, kids: draft.kids.slice(0, target) };
  const kids = [...draft.kids];
  while (kids.length < target) {
    const free = nicknames.find((n) => !kids.some((k) => sameText(k.nickname, n)));
    const kid = newKid(nextKidKey(kids), free ?? "");
    kids.push(free === undefined ? { ...kid, custom: true } : kid);
  }
  return { ...draft, kids };
}

/** A key no kid of the draft has. Counted, not random, so the server and the browser agree. */
export function nextKidKey(kids: KidDraft[]): string {
  const numbers = kids.map((k) => Number(k.key.replace("kid-", ""))).filter(Number.isFinite);
  return `kid-${numbers.length ? Math.max(...numbers) + 1 : 0}`;
}

export function validateSetup(draft: SetupDraft): SetupErrors {
  const errors: SetupErrors = {};
  const kid: Record<string, KidError> = {};
  for (const { key, nickname, age } of draft.kids) {
    const name = nickname.trim();
    if (!name) kid[key] = "nicknameMissing";
    else if (name.length > MAX_NICKNAME) kid[key] = "nicknameTooLong";
    else if (!isAge(age)) kid[key] = "ageInvalid";
  }
  if (Object.keys(kid).length) errors.kid = kid;

  // The parent reads the nicknames aloud, so the backend refuses two that sound the same.
  const names = draft.kids.map((k) => k.nickname.trim().toLocaleLowerCase()).filter(Boolean);
  if (new Set(names).size !== names.length) errors.kids = "repeated";

  if (draft.rooms.length === 0) errors.rooms = "missing";
  else if (draft.rooms.length > MAX_ROOMS) errors.rooms = "tooMany";
  if (draft.objects.length < MIN_OBJECTS) errors.objects = "tooFew";
  else if (draft.objects.length > MAX_OBJECTS) errors.objects = "tooMany";
  return errors;
}

export function hasErrors(errors: SetupErrors): boolean {
  return Object.keys(errors).length > 0;
}

export function toFamilyCreate(draft: SetupDraft): FamilyCreate {
  return {
    kids: draft.kids.map((k) => ({ nickname: k.nickname.trim(), age: Number(k.age) })),
    rooms: draft.rooms,
    objects: draft.objects,
  };
}

/** Adds the label, or takes it away when it is already there. Case and spaces don't count. */
export function toggleLabel(labels: string[], label: string): string[] {
  const clean = label.trim().replace(/\s+/g, " ").slice(0, MAX_LABEL);
  if (!clean) return labels;
  const same = (l: string) => l.toLocaleLowerCase() === clean.toLocaleLowerCase();
  return labels.some(same) ? labels.filter((l) => !same(l)) : [...labels, clean];
}

function isAge(value: string): boolean {
  if (!/^\d{1,2}$/.test(value.trim())) return false;
  const age = Number(value);
  return age >= MIN_AGE && age <= MAX_AGE;
}
