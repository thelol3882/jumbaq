import type { Schemas } from "@/shared/api/types";

export type Family = Schemas["FamilyOut"];
/** The family as `GET /family` gives it: also what the server allows, like demo mode. */
export type FamilyState = Schemas["FamilyStateOut"];
export type Kid = Schemas["KidOut"];
export type FamilyCreate = Schemas["FamilyCreate"];
export type KidIn = Schemas["KidIn"];
