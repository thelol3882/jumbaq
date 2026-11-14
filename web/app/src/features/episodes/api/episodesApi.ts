import { baseApi } from "@/shared/api/baseApi";
import type { Episode } from "../types";

const episodeChanged = (id: string) => [{ type: "Episode" as const, id }, "Case" as const];

export const episodesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // `content` is null while the episode is written or not yet available.
    getEpisode: builder.query<Episode, string>({
      query: (episodeId) => `/episodes/${episodeId}`,
      providesTags: (_result, _error, episodeId) => [{ type: "Episode", id: episodeId }],
    }),
    // The answer makes the episode played: the result and the new clue come back with it.
    answerEpisode: builder.mutation<Episode, { episodeId: string; answer: string }>({
      query: ({ episodeId, answer }) => ({ url: `/episodes/${episodeId}/answer`, method: "POST", body: { answer } }),
      invalidatesTags: (_result, _error, { episodeId }) => episodeChanged(episodeId),
    }),
    // The other riddle, for an object the family doesn't have. Once per episode.
    swapRiddle: builder.mutation<Episode, string>({
      query: (episodeId) => ({ url: `/episodes/${episodeId}/swap`, method: "POST" }),
      invalidatesTags: (_result, _error, episodeId) => [{ type: "Episode", id: episodeId }],
    }),
    // Only when the server runs in demo mode: the jury plays five evenings in five minutes.
    openNow: builder.mutation<Episode, string>({
      query: (episodeId) => ({ url: `/episodes/${episodeId}/open-now`, method: "POST" }),
      invalidatesTags: (_result, _error, episodeId) => episodeChanged(episodeId),
    }),
  }),
});

export const { useGetEpisodeQuery, useAnswerEpisodeMutation, useSwapRiddleMutation, useOpenNowMutation } =
  episodesApi;
