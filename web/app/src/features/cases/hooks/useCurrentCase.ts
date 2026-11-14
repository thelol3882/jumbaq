import { toApiError } from "@/shared/api/errors";
import { useRefetchWhile } from "@/shared/hooks/useRefetchWhile";
import { useGetCurrentCaseQuery } from "../api/casesApi";
import { isBeingWritten } from "../services/caseBoard";

/**
 * The family's current case. While the worker is still writing (the case is planned, the
 * next evening is generated, or case 1 is not opened yet) it asks again every few seconds.
 * `skip` keeps a screen that only shows the case to a known family from asking before it has one.
 */
export function useCurrentCase({ skip = false }: { skip?: boolean } = {}) {
  const query = useGetCurrentCaseQuery(undefined, { skip });
  const notOpenedYet = query.isError && toApiError(query.error).code === "case.not_found";
  const writing = notOpenedYet || (query.data ? isBeingWritten(query.data) : false);
  const progress = query.data ? [query.data.status, ...query.data.episodes.map((e) => e.status)].join(":") : "none";
  const { slow } = useRefetchWhile(writing, query.refetch, progress);

  return {
    current: query.data,
    loading: query.isLoading,
    writing,
    slow,
    error: query.isError && !notOpenedYet ? query.error : undefined,
    retry: query.refetch,
  };
}
