import { useState } from "react";
import { toApiError } from "@/shared/api/errors";
import { useSkipEpisodeMutation } from "../api/episodesApi";

/** The demo shortcut: plays an evening out. `refused` when the server is no longer in demo mode. */
export function useSkipEvening() {
  const [skipEpisode, state] = useSkipEpisodeMutation();
  const [refused, setRefused] = useState(false);

  const skip = async (episodeId: string) => {
    try {
      await skipEpisode(episodeId).unwrap();
    } catch (error) {
      if (toApiError(error).code === "episode.demo_mode_off") setRefused(true);
    }
  };

  return { skip, skipping: state.isLoading, refused, error: refused ? undefined : state.error };
}
