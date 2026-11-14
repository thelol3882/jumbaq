"use client";

import { useTranslations } from "next-intl";
import type { Riddle } from "../types";

/** For the grown-up only, marked so it is never read out by mistake. */
export function ParentNote({ riddle }: { riddle: Riddle }) {
  const t = useTranslations("episodes");
  return (
    <aside aria-label={t("notAloud")} className="flex flex-col gap-2">
      <p className="font-type text-case text-note-fg">{t("notAloud")}</p>
      <p className="font-hand text-note text-note-fg">{riddle.parent_note}</p>
    </aside>
  );
}
