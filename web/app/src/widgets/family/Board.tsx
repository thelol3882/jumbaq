"use client";

import { useTranslations } from "next-intl";
import { EvidenceList, SuspectTable, type Case } from "@/features/cases";

/** The suspects and the evidence so far. Empty while the case is planned. */
export function Board({ current }: { current: Case }) {
  const t = useTranslations("widget.family");
  if (current.suspects.length === 0) return null;
  return (
    <>
      <section aria-labelledby="board-suspects">
        <h2 id="board-suspects" className="mb-2.5 font-type text-label font-normal text-ink-muted">
          {t("suspects")}
        </h2>
        <SuspectTable suspects={current.suspects} clues={current.clues} />
      </section>
      <section aria-labelledby="board-evidence">
        <h2 id="board-evidence" className="mb-2.5 font-type text-label font-normal text-ink-muted">
          {t("evidence")}
        </h2>
        <EvidenceList clues={current.clues} />
      </section>
    </>
  );
}
