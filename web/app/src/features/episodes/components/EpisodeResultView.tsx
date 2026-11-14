"use client";

import { useTranslations } from "next-intl";
import { EvidenceTag, HandNote } from "@/shared/components/notebook";
import type { EpisodeResult } from "../types";

function Tick() {
  return (
    <svg aria-hidden="true" width="36" height="32" viewBox="0 0 30 26">
      <path d="M3 14 L11 22 L27 3" stroke="var(--color-accent-red)" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** After the answer: what it meant, read aloud, and how the story goes on. */
export function EpisodeResultView({ result, large = false }: { result: EpisodeResult; large?: boolean }) {
  const t = useTranslations("episodes");
  const aloud = large ? "text-[1.625rem] leading-[1.6]" : "text-aloud";
  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-3.5">
        <span className="font-type text-case font-normal">{t("result.logged")}</span>
        <span className="-rotate-4 font-hand text-note-answer text-note-fg">{result.answer}</span>
        <Tick />
      </div>
      <div className="relative mt-6 flex max-w-[34em] flex-col gap-5">
        <span aria-hidden="true" className="absolute top-1 -left-12 rotate-180 font-type text-label-sm text-aloud-label [writing-mode:vertical-rl]">
          {t("readAloud")}
        </span>
        <p className={`font-story ${aloud}`}>{result.resolution}</p>
        <p className={`font-story ${aloud}`}>{result.cliffhanger}</p>
      </div>
      <HandNote className="mt-2 ml-28 -rotate-2">{t("result.continued")}</HandNote>
    </div>
  );
}

/** The clue of tonight on its manila tag. Always the clue of the plan, never the model's words. */
export function ClueTag({ number, text }: { number: number; text: string }) {
  const t = useTranslations("episodes");
  return (
    <div className="w-[min(21rem,100%)] -rotate-2">
      <EvidenceTag label={t("result.exhibit", { number })}>
        <span className="text-[1.5rem] leading-[1.25] font-bold">{text}</span>
      </EvidenceTag>
    </div>
  );
}
