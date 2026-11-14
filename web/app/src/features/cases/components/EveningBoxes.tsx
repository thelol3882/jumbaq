"use client";

import { useTranslations } from "next-intl";
import type { CaseEpisode } from "../types";
import { nextEvening, playedCount } from "../services/caseBoard";

function Tick() {
  return (
    <svg aria-hidden="true" width="22" height="20" viewBox="0 0 30 26">
      <path d="M3 14 L11 22 L27 3" stroke="var(--color-accent-red)" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** One box per evening, ticked when played; the next evening has a red frame. */
export function EveningBoxes({ episodes }: { episodes: readonly CaseEpisode[] }) {
  const t = useTranslations("cases");
  const next = nextEvening(episodes)?.number;
  return (
    <div className="flex items-center gap-2" role="img" aria-label={t("progress", { played: playedCount(episodes), total: episodes.length })}>
      {episodes.map((e) => (
        <span
          key={e.number}
          className={`flex size-8.5 items-center justify-center border-2 font-type text-label ${
            e.number === next ? "border-accent-red font-bold text-accent-red" : "border-ink text-ink-faint"
          }`}
        >
          {e.status === "played" ? <Tick /> : e.number}
        </span>
      ))}
    </div>
  );
}
