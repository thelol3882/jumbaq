"use client";

import { useTranslations } from "next-intl";
import type { Certificate } from "../types";

/** The certificate the kids keep. Printing shows only this card (see globals.css). */
export function CertificateCard({ certificate, solvedOn }: { certificate: Certificate; solvedOn: string }) {
  const t = useTranslations("cases");
  const names = certificate.nicknames;
  const last = names.at(-1) ?? "";
  const first = names.slice(0, -1).join(", ");
  return (
    <figure data-print="certificate" aria-label={t("certificate.label")} className="relative m-0 rotate-1">
      <span aria-hidden="true" className="absolute -top-2 -left-3.5 h-5.5 w-17.5 -rotate-[35deg] bg-tag-tape print:hidden" />
      <span aria-hidden="true" className="absolute -top-2 -right-3.5 h-5.5 w-17.5 rotate-[35deg] bg-tag-tape print:hidden" />
      <div className="border border-rule-card bg-paper-card px-7 pt-7.5 pb-6">
        <p className="font-type text-label text-ink-muted">{t("certificate.title")}</p>
        <p className="mt-3 text-body-sm">{t("certificate.intro")}</p>
        <p className="mt-2 font-type text-[2.125rem] leading-[1.15] font-bold">
          {first ? (
            <>
              {first} <span className="text-lg font-normal">{t("certificate.and")}</span> {last}
            </>
          ) : (
            last
          )}
        </p>
        <p className="mt-2.5 text-body-sm">
          {t("certificate.solved", { title: certificate.title, rank: t(`ranks.${certificate.rank}`) })}
        </p>
        <div className="mt-7 flex justify-between gap-4">
          <span className="flex-1 border-t-[1.5px] border-ink pt-1 font-type text-xs">{t("certificate.chief")}</span>
          <span className="flex-1 border-t-[1.5px] border-ink pt-1 font-type text-xs">{solvedOn}</span>
        </div>
      </div>
    </figure>
  );
}
