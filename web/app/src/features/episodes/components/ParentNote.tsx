"use client";

import { useTranslations } from "next-intl";
import { HandNote } from "@/shared/components/notebook";
import type { Riddle } from "../types";

/** For the grown-up only, marked so it is never read out by mistake. */
export function ParentNote({ riddle }: { riddle: Riddle }) {
  const t = useTranslations("episodes");
  return (
    <aside aria-label={t("notAloud")} className="flex flex-col gap-2">
      <p className="font-type text-case text-note-fg">{t("notAloud")}</p>
      <HandNote>{riddle.parent_note}</HandNote>
    </aside>
  );
}
