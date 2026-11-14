import { toApiError } from "@/shared/api/errors";
import { casesApi, useGetCurrentCaseQuery } from "../api/casesApi";
import { isBeingWritten } from "../services/caseBoard";

const POLL_MS = 3000;

function stillWriting(state: { isError: boolean; error?: unknown; data?: Parameters<typeof isBeingWritten>[0] }) {
  if (state.isError) return toApiError(state.error).code === "case.not_found";
  return state.data ? isBeingWritten(state.data) : false;
}

/**
 * The family's current case. While the worker is still writing (the case is planned, the
 * next evening is generated, or case 1 is not opened yet) it asks again every few seconds.
 */
export function useCurrentCase() {
  // The cached answer decides the polling of the same render.
  const cached = casesApi.endpoints.getCurrentCase.useQueryState();
  const query = useGetCurrentCaseQuery(undefined, { pollingInterval: stillWriting(cached) ? POLL_MS : 0 });
  const notOpenedYet = query.isError && toApiError(query.error).code === "case.not_found";

  return {
    current: query.data,
    loading: query.isLoading,
    writing: stillWriting(query),
    error: query.isError && !notOpenedYet ? query.error : undefined,
    retry: query.refetch,
  };
}
