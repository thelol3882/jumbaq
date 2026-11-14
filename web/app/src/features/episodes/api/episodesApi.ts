import { baseApi } from "@/shared/api/baseApi";
import type { Episode } from "../types";

const episodeOnly = (id: string) => [{ type: "Episode" as const, id }];
const episodeChanged = (id: string) => [...episodeOnly(id), "Case" as const];

export const episodesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // `content` is null while the episode is written or not yet available.
    getEpisode: builder.query<Episode, string>({
      query: (episodeId) => `/episodes/${episodeId}`,
      providesTags: (_result, _error, episodeId) => [{ type: "Episode", id: episodeId }],
    }),
    // The answer only moves the evening on to the decode step; the episode is not played yet.
    answerEpisode: builder.mutation<Episode, { episodeId: string; answer: string }>({
      query: ({ episodeId, answer }) => ({ url: `/episodes/${episodeId}/answer`, method: "POST", body: { answer } }),
      invalidatesTags: (_result, _error, { episodeId }) => episodeOnly(episodeId),
    }),
    // A wrong word is a 200 with one more attempt; the second wrong one gives the word away.
    decodeEpisode: builder.mutation<Episode, { episodeId: string; word: string | null }>({
      query: ({ episodeId, word }) => ({ url: `/episodes/${episodeId}/decode`, method: "POST", body: { word } }),
      invalidatesTags: (_result, _error, { episodeId }) => episodeOnly(episodeId),
    }),
    // The strike plays the episode: the result and the new clue come back with it.
    strikeSuspect: builder.mutation<Episode, { episodeId: string; suspectId: string }>({
      query: ({ episodeId, suspectId }) => ({
        url: `/episodes/${episodeId}/strike`,
        method: "POST",
        body: { suspect_id: suspectId },
      }),
      invalidatesTags: (_result, _error, { episodeId }) => episodeChanged(episodeId),
    }),
    // The other riddle, for an object the family doesn't have. Once per episode.
    swapRiddle: builder.mutation<Episode, string>({
      query: (episodeId) => ({ url: `/episodes/${episodeId}/swap`, method: "POST" }),
      invalidatesTags: (_result, _error, episodeId) => episodeOnly(episodeId),
    }),
    // Only when the server runs in demo mode: the jury plays five evenings in five minutes.
    openNow: builder.mutation<Episode, string>({
      query: (episodeId) => ({ url: `/episodes/${episodeId}/open-now`, method: "POST" }),
      invalidatesTags: (_result, _error, episodeId) => episodeChanged(episodeId),
    }),
    // Demo mode too: plays the rest of an available evening with the right answers.
    skipEpisode: builder.mutation<Episode, string>({
      query: (episodeId) => ({ url: `/episodes/${episodeId}/skip`, method: "POST" }),
      invalidatesTags: (_result, _error, episodeId) => episodeChanged(episodeId),
    }),
  }),
});

export const {
  useGetEpisodeQuery,
  useAnswerEpisodeMutation,
  useDecodeEpisodeMutation,
  useStrikeSuspectMutation,
  useSwapRiddleMutation,
  useOpenNowMutation,
  useSkipEpisodeMutation,
} = episodesApi;
