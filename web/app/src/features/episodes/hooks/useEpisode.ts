import { skipToken } from "@reduxjs/toolkit/query";
import { useRefetchWhile } from "@/shared/hooks/useRefetchWhile";
import { useGetEpisodeQuery } from "../api/episodesApi";

/** One episode. While the worker writes it, it asks again every few seconds. */
export function useEpisode(episodeId: string | null) {
  const query = useGetEpisodeQuery(episodeId ?? skipToken);
  const status = query.data?.status;
  const writing = status === "requested" || status === "generating";
  const { slow } = useRefetchWhile(writing && episodeId !== null, query.refetch, status);

  return { episode: query.data, loading: query.isLoading, writing, slow, error: query.error, retry: query.refetch };
}
