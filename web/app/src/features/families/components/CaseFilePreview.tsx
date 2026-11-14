"use client";

import { useFormatter, useTranslations } from "next-intl";
import type { SetupDraft } from "../services/setupForm";

/** The manila case file filling in while the parent answers the setup. */
export function CaseFilePreview({ draft }: { draft: SetupDraft }) {
  const t = useTranslations("families");
  const format = useFormatter();
  const kids = draft.kids.filter((k) => k.nickname.trim());
  const empty = <span className="font-type text-label text-tag-ink">{t("preview.empty")}</span>;

  return (
    <div className="relative rotate-1">
      <span aria-hidden="true" className="absolute -top-3 left-10 z-10 h-6 w-20 -rotate-3 bg-tag-tape" />
      <div className="bg-evidence-bg px-6.5 pt-6.5 pb-5.5" aria-live="polite">
        <p className="font-type text-label-sm text-evidence-label">{t("preview.label")}</p>
        <dl className="mt-4 grid grid-cols-[120px_minmax(0,1fr)] gap-x-3 gap-y-3.5">
          <dt className="font-type text-label font-bold text-evidence-label">{t("kids.title")}</dt>
          <dd className="text-[1.1875rem] leading-[1.35] font-semibold">
            {kids.length
              ? kids.map((k) => (
                  <span key={k.key} className="block">
                    {k.age.trim() ? t("preview.kid", { nickname: k.nickname.trim(), age: k.age.trim() }) : k.nickname.trim()}
                  </span>
                ))
              : empty}
          </dd>
          <dt className="font-type text-label font-bold text-evidence-label">{t("rooms.title")}</dt>
          <dd className="text-[1.1875rem] leading-[1.35]">{draft.rooms.length ? format.list(draft.rooms) : empty}</dd>
          <dt className="font-type text-label font-bold text-evidence-label">{t("objects.title")}</dt>
          <dd className="text-[1.1875rem] leading-[1.35]">{draft.objects.length ? format.list(draft.objects) : empty}</dd>
        </dl>
      </div>
    </div>
  );
}
