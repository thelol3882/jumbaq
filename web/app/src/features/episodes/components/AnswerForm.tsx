"use client";

import { useTranslations } from "next-intl";
import { useId } from "react";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, StampButton, TypedButton } from "@/shared/components/notebook";
import { MAX_ANSWER, useAnswerForm } from "../hooks/useAnswerForm";
import type { EpisodeContent } from "../types";

/** Straight under the riddle: what the kids found, then the stamp. Hint and the other riddle below. */
export function AnswerForm({ episodeId, content }: { episodeId: string; content: EpisodeContent }) {
  const t = useTranslations("episodes");
  const errorMessage = useApiErrorMessage();
  const form = useAnswerForm(episodeId);
  const inputId = useId();

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void form.submit();
      }}
      className="flex max-w-[40rem] flex-col gap-3"
    >
      <label htmlFor={inputId} className="font-type text-case">
        {t("answer.label")}
      </label>
      <div className="flex flex-wrap items-stretch gap-3.5">
        <input
          id={inputId}
          value={form.answer}
          maxLength={MAX_ANSWER}
          autoComplete="off"
          placeholder={t("answer.placeholder")}
          onChange={(e) => form.setAnswer(e.target.value)}
          className="h-17 min-w-0 flex-[1_1_16rem] rounded-sm border border-rule-card bg-paper-card px-4 font-hand text-[1.625rem] text-note-fg placeholder:font-story placeholder:text-body-sm placeholder:text-ink-faint"
        />
        <div className="flex-[0_0_auto]">
          <StampButton type="submit" disabled={!form.canSubmit} className="px-7 whitespace-nowrap">
            {form.sending ? t("answer.sending") : t("answer.submit")}
          </StampButton>
        </div>
      </div>
      {form.error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(form.error)}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-7">
        <TypedButton aria-expanded={form.showHint} onClick={form.toggleHint}>
          {form.showHint ? t("hint.hide") : t("hint.show")}
        </TypedButton>
        {content.swapped ? null : (
          <TypedButton disabled={form.swapping} onClick={() => void form.swapRiddle()}>
            {t("swap")}
          </TypedButton>
        )}
      </div>
      {form.showHint ? <HandNote lead={t("hint.lead")}>{content.hint}</HandNote> : null}
    </form>
  );
}
