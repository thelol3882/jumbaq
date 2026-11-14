"use client";

import { useTranslations } from "next-intl";
import type { Clue } from "../types";

/** The clues found so far, in the order of the evenings. Read aloud before the accusation. */
export function EvidenceList({ clues, large = false }: { clues: readonly Clue[]; large?: boolean }) {
  const t = useTranslations("cases");
  if (clues.length === 0) return <p className="font-hand text-note-sm text-note-fg">{t("noEvidence")}</p>;
  return (
    <ol className="flex flex-col gap-2.5">
      {clues.map((c) => (
        <li key={c.episode} className={`grid grid-cols-[30px_minmax(0,1fr)] items-start ${large ? "text-[1.5rem] leading-[1.5]" : "text-body-sm"}`}>
          <svg aria-hidden="true" width="22" height="20" viewBox="0 0 30 26" className={large ? "mt-2" : "mt-1"}>
            <path d="M3 14 L11 22 L27 3" stroke="var(--color-accent-red)" strokeWidth="3.4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>{c.text}</span>
        </li>
      ))}
    </ol>
  );
}
