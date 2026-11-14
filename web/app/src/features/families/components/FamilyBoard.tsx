"use client";

import { useTranslations } from "next-intl";
import { EvidenceTag } from "@/shared/components/notebook";
import type { Family } from "../types";

/** The right page of the case file on a wide screen: who plays, where, and with what. */
export function FamilyBoard({ family }: { family: Family }) {
  const t = useTranslations("families");
  return (
    <>
      <section aria-labelledby="board-detectives">
        <h2 id="board-detectives" className="mb-2.5 font-type text-label font-normal text-ink-muted">
          {t("summary.detectives")}
        </h2>
        <ul className="rotate-[0.4deg] border-2 border-suspect-border bg-suspect-bg">
          {family.kids.map((kid) => (
            <li
              key={kid.id}
              className="flex items-center justify-between gap-3 border-b-[1.5px] border-suspect-border px-3.5 py-3 last:border-b-0"
            >
              <span className="font-type text-suspect">{kid.nickname}</span>
              <span className="font-hand text-note-sm text-suspect-note">{t("summary.age", { age: kid.age })}</span>
            </li>
          ))}
        </ul>
      </section>
      <div className="w-72 -rotate-2">
        <EvidenceTag label={t("summary.scene")}>{family.rooms.join(", ")}</EvidenceTag>
      </div>
      <section aria-labelledby="board-evidence">
        <h2 id="board-evidence" className="mb-2.5 font-type text-label font-normal text-ink-muted">
          {t("summary.evidence")}
        </h2>
        <ul className="flex flex-wrap gap-2">
          {family.objects.map((object) => (
            <li key={object} className="rounded-sm border border-rule-card bg-paper-card px-3 py-1.5 font-type text-case font-normal">
              {object}
            </li>
          ))}
        </ul>
      </section>
    </>
  );
}
