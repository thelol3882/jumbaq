import { useState } from "react";
import { useAnswerEpisodeMutation, useSwapRiddleMutation } from "../api/episodesApi";
import { charactersLeft, MAX_ANSWER } from "../services/answerLimit";

/** What the kids found, typed by the parent, plus the hint and the other riddle. */
export function useAnswerForm(episodeId: string) {
  const [answer, setAnswer] = useState("");
  const [showHint, setShowHint] = useState(false);
  const [send, sending] = useAnswerEpisodeMutation();
  const [swap, swapping] = useSwapRiddleMutation();

  const clean = answer.replace(/\s+/g, " ").trim();

  const submit = async () => {
    if (!clean) return;
    try {
      await send({ episodeId, answer: clean }).unwrap();
    } catch {
      // `error` holds it for the form
    }
  };

  const swapRiddle = async () => {
    try {
      await swap(episodeId).unwrap();
      setShowHint(false);
    } catch {
      // `error` holds it for the form
    }
  };

  return {
    answer,
    setAnswer: (value: string) => setAnswer(value.slice(0, MAX_ANSWER)),
    left: charactersLeft(answer.length),
    canSubmit: clean.length > 0 && !sending.isLoading,
    submit,
    sending: sending.isLoading,
    showHint,
    toggleHint: () => setShowHint((v) => !v),
    swapRiddle,
    swapping: swapping.isLoading,
    error: sending.error ?? swapping.error,
  };
}
