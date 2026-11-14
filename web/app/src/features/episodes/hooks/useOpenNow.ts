import { useState } from "react";
import { toApiError } from "@/shared/api/errors";
import { useOpenNowMutation } from "../api/episodesApi";

/** The demo shortcut: opens a waiting evening now. `refused` when the server is no longer in demo mode. */
export function useOpenNow() {
  const [openNow, state] = useOpenNowMutation();
  const [refused, setRefused] = useState(false);

  const open = async (episodeId: string) => {
    try {
      await openNow(episodeId).unwrap();
    } catch (error) {
      if (toApiError(error).code === "episode.demo_mode_off") setRefused(true);
    }
  };

  return { open, opening: state.isLoading, refused, error: refused ? undefined : state.error };
}
