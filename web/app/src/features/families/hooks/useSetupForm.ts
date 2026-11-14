import { useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { setFamilyHint } from "@/shared/session/familyHint";
import { useCreateFamilyMutation } from "../api/familiesApi";
import { DEFAULT_OBJECTS, DEFAULT_ROOMS, NICKNAME_PRESETS } from "../services/presets";
import {
  emptyDraft,
  hasErrors,
  setKidCount,
  toFamilyCreate,
  toggleLabel,
  validateSetup,
  type KidDraft,
} from "../services/setupForm";

/** The one-minute setup: the draft, its checks and the submit. */
export function useSetupForm(onCreated: () => void) {
  const t = useTranslations("families");
  const nicknames = NICKNAME_PRESETS.map((key) => t(`kids.presets.${key}`));
  const [draft, setDraft] = useState(() =>
    emptyDraft({
      nicknames,
      rooms: DEFAULT_ROOMS.map((key) => t(`rooms.presets.${key}`)),
      objects: DEFAULT_OBJECTS.map((key) => t(`objects.presets.${key}`)),
    }),
  );
  const [tried, setTried] = useState(false);
  // Counts the tries that the checks stopped, so the form can show the first problem.
  const [blocked, setBlocked] = useState(0);
  const [createFamily, { isLoading, error }] = useCreateFamilyMutation();

  const errors = useMemo(() => validateSetup(draft), [draft]);

  const setKid = (key: string, changes: Partial<Omit<KidDraft, "key">>) =>
    setDraft((d) => ({ ...d, kids: d.kids.map((k) => (k.key === key ? { ...k, ...changes } : k)) }));

  const setKidsCount = (count: number) => setDraft((d) => setKidCount(d, count, nicknames));

  const toggleRoom = (label: string) => setDraft((d) => ({ ...d, rooms: toggleLabel(d.rooms, label) }));
  const toggleObject = (label: string) =>
    setDraft((d) => ({ ...d, objects: toggleLabel(d.objects, label) }));

  const submit = async () => {
    setTried(true);
    if (hasErrors(errors)) {
      setBlocked((n) => n + 1);
      return;
    }
    try {
      await createFamily(toFamilyCreate(draft)).unwrap();
    } catch {
      return; // `error` holds it for the form
    }
    setFamilyHint(true);
    onCreated();
  };

  return {
    draft,
    // Shown only after the first try, so an empty form does not start full of errors.
    errors: tried ? errors : {},
    blocked,
    nicknames,
    setKid,
    setKidsCount,
    toggleRoom,
    toggleObject,
    submit,
    saving: isLoading,
    error,
  };
}

export type SetupFormState = ReturnType<typeof useSetupForm>;
