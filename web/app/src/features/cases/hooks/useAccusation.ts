import { useState } from "react";
import { useAccuseMutation } from "../api/casesApi";
import type { Accusation } from "../types";

/** The pick of the kids and the accusation. A wrong pick only leaves a note; no losing. */
export function useAccusation(caseId: string) {
  const [picked, setPicked] = useState<string | null>(null);
  const [wrongPick, setWrongPick] = useState<string | null>(null);
  const [accuse, { isLoading, error, data }] = useAccuseMutation();

  const submit = async (): Promise<Accusation | undefined> => {
    if (!picked) return undefined;
    let result: Accusation;
    try {
      result = await accuse({ caseId, suspectId: picked }).unwrap();
    } catch {
      return undefined; // `error` holds it for the form
    }
    setWrongPick(result.correct ? null : picked);
    return result;
  };

  return { picked, pick: setPicked, wrongPick, submit, accusing: isLoading, error, result: data };
}
