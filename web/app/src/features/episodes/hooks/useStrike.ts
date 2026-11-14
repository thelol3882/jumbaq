import { useStrikeSuspectMutation } from "../api/episodesApi";

/** Sends the suspect the kids crossed out. */
export function useStrike(episodeId: string) {
  const [send, state] = useStrikeSuspectMutation();
  const pick = async (suspectId: string) => {
    try {
      await send({ episodeId, suspectId }).unwrap();
    } catch {
      // `error` holds it for the step
    }
  };
  return { pick, sending: state.isLoading, error: state.error };
}
