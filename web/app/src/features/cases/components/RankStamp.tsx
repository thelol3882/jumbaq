"use client";

import { useTranslations } from "next-intl";
import type { Rank } from "../types";

export function RankStamp({ rank }: { rank: Rank }) {
  const t = useTranslations("cases");
  return (
    <div className="w-fit -rotate-6 border-4 border-success-border px-5.5 py-4 text-success-fg outline-[1.5px] -outline-offset-[10px] outline-success-border">
      <p className="font-type text-label">{t("rankAwarded")}</p>
      <p className="mt-0.5 font-type text-[2rem] leading-none font-bold tracking-[0.02em] whitespace-nowrap">
        {t(`ranks.${rank}`)}
      </p>
    </div>
  );
}
