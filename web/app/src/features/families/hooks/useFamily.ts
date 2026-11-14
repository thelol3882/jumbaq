import { useEffect } from "react";
import { toApiError } from "@/shared/api/errors";
import { setFamilyHint } from "@/shared/session/familyHint";
import { useGetFamilyQuery } from "../api/familiesApi";

/**
 * The family of this browser. `missing` when it has none, so the screen offers the setup.
 * `skip` keeps a screen open to visitors from asking when the hint says there is no family.
 */
export function useFamily({ skip = false }: { skip?: boolean } = {}) {
  const query = useGetFamilyQuery(undefined, { skip });
  const missing = query.isError && toApiError(query.error).code === "family.no_session";

  useEffect(() => {
    if (missing) setFamilyHint(false);
    if (query.isSuccess) setFamilyHint(true);
  }, [missing, query.isSuccess]);

  return { family: query.data, loading: query.isLoading, missing, error: missing ? undefined : query.error, retry: query.refetch };
}
