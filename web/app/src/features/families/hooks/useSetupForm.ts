import { useMemo, useState } from "react";
import { setFamilyHint } from "@/shared/session/familyHint";
import { useCreateFamilyMutation } from "../api/familiesApi";
import {
  emptyDraft,
  hasErrors,
  MAX_KIDS,
  nextKidKey,
  toFamilyCreate,
  toggleLabel,
  validateSetup,
  type KidDraft,
} from "../services/setupForm";

/** The one-minute setup: the draft, its checks and the submit. */
export function useSetupForm(onCreated: () => void) {
  const [draft, setDraft] = useState(emptyDraft);
  const [tried, setTried] = useState(false);
  const [createFamily, { isLoading, error }] = useCreateFamilyMutation();

  const errors = useMemo(() => validateSetup(draft), [draft]);

  const setKid = (key: string, changes: Partial<Omit<KidDraft, "key">>) =>
    setDraft((d) => ({ ...d, kids: d.kids.map((k) => (k.key === key ? { ...k, ...changes } : k)) }));

  const addKid = () =>
    setDraft((d) =>
      d.kids.length >= MAX_KIDS
        ? d
        : { ...d, kids: [...d.kids, { key: nextKidKey(d.kids), nickname: "", age: "" }] },
    );

  const removeKid = (key: string) =>
    setDraft((d) => (d.kids.length <= 1 ? d : { ...d, kids: d.kids.filter((k) => k.key !== key) }));

  const toggleRoom = (label: string) => setDraft((d) => ({ ...d, rooms: toggleLabel(d.rooms, label) }));
  const toggleObject = (label: string) =>
    setDraft((d) => ({ ...d, objects: toggleLabel(d.objects, label) }));

  const submit = async () => {
    setTried(true);
    if (hasErrors(errors)) return;
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
    // Shown only after the first try, so an empty form does not start in red.
    errors: tried ? errors : {},
    canAddKid: draft.kids.length < MAX_KIDS,
    setKid,
    addKid,
    removeKid,
    toggleRoom,
    toggleObject,
    submit,
    saving: isLoading,
    error,
  };
}

export type SetupFormState = ReturnType<typeof useSetupForm>;
