"use client";

import { useTranslations } from "next-intl";
import type { Clue, Suspect } from "../types";
import { suspectMark, type SuspectMark } from "../services/caseBoard";

const MARK_TEXT = { cleared: "cleared", pointed: "pointedAt", suspect: "stillSuspect" } as const satisfies Record<SuspectMark, string>;

/** The suspects as the kids see them: a red pencil line through each one a clue cleared. */
export function SuspectTable({ suspects, clues }: { suspects: readonly Suspect[]; clues: readonly Clue[] }) {
  const t = useTranslations("cases");
  return (
    <ul className="rotate-[0.4deg] border-2 border-suspect-border bg-suspect-bg">
      {suspects.map((s) => {
        const mark = suspectMark(s.id, clues);
        const cleared = mark === "cleared";
        return (
          <li key={s.id} className="flex items-center justify-between gap-3 border-b-[1.5px] border-suspect-border px-3.5 py-3 last:border-b-0">
            <span className={`relative font-type text-suspect ${cleared ? "text-cleared-fg" : "text-suspect-fg"}`}>
              {s.name}
              {cleared ? (
                <svg aria-hidden="true" viewBox="0 0 120 16" preserveAspectRatio="none" className="absolute inset-x-[-4px] top-1/2 h-4 w-[calc(100%+8px)] -translate-y-1/2">
                  <path d="M2 10 C 40 4, 80 12, 118 5" stroke="var(--color-cleared-strike)" strokeWidth="2.8" fill="none" strokeLinecap="round" />
                </svg>
              ) : null}
            </span>
            <span className="font-hand text-note-sm text-suspect-note">{t(MARK_TEXT[mark])}</span>
          </li>
        );
      })}
    </ul>
  );
}
