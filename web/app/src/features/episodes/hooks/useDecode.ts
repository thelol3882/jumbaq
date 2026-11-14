import { useDecodeEpisodeMutation } from "../api/episodesApi";

/** Sends the picked word, or null for the youngest kids who only count. */
export function useDecode(episodeId: string) {
  const [send, state] = useDecodeEpisodeMutation();
  const pick = async (word: string | null) => {
    try {
      await send({ episodeId, word }).unwrap();
    } catch {
      // `error` holds it for the step
    }
  };
  return { pick, sending: state.isLoading, error: state.error };
}
