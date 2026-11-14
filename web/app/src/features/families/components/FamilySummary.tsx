"use client";

import { useTranslations } from "next-intl";
import { EvidenceTag } from "@/shared/components/notebook";
import type { Family } from "../types";

/** The case file of the family: who plays, and where the riddles may point. */
export function FamilySummary({ family }: { family: Family }) {
  const t = useTranslations("families");
  return (
    <div className="flex flex-col gap-6">
      <section aria-labelledby="detectives" className="flex flex-col gap-2">
        <h2 id="detectives" className="font-type text-case text-accent-red">
          {t("summary.detectives")}
        </h2>
        <ul className="flex flex-col gap-1">
          {family.kids.map((kid) => (
            <li key={kid.id} className="text-body">
              {t.rich("summary.kid", {
                nickname: kid.nickname,
                age: kid.age,
                name: (chunks) => <span className="font-semibold">{chunks}</span>,
                aside: (chunks) => <span className="font-type text-label text-ink-muted">{chunks}</span>,
              })}
            </li>
          ))}
        </ul>
      </section>
      <div className="ml-auto w-64 rotate-[2.5deg]">
        <EvidenceTag label={t("summary.scene")}>
          {t("summary.places", { rooms: family.rooms.length, objects: family.objects.length })}
        </EvidenceTag>
      </div>
    </div>
  );
}
