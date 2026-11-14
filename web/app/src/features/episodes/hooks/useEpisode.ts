import { skipToken } from "@reduxjs/toolkit/query";
import { episodesApi, useGetEpisodeQuery } from "../api/episodesApi";
import type { Episode } from "../types";

const POLL_MS = 3000;

const isWriting = (episode: Episode | undefined) =>
  episode?.status === "requested" || episode?.status === "generating";

/** One episode. While the worker writes it, it asks again every few seconds. */
export function useEpisode(episodeId: string | null) {
  const arg = episodeId ?? skipToken;
  // The cached answer decides the polling of the same render.
  const cached = episodesApi.endpoints.getEpisode.useQueryState(arg);
  const query = useGetEpisodeQuery(arg, { pollingInterval: isWriting(cached.data) ? POLL_MS : 0 });

  return {
    episode: query.data,
    loading: query.isLoading,
    writing: isWriting(query.data),
    error: query.error,
    retry: query.refetch,
  };
}
