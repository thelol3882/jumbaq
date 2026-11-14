"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import type { SolvedCase } from "../types";

/** The cases the family has solved, each with a link to its certificate. Show it only when there are some. */
export function PastCases({ cases }: { cases: readonly SolvedCase[] }) {
  const t = useTranslations("cases");
  return (
    <section aria-labelledby="past-cases">
      <h2 id="past-cases" className="mb-2.5 font-type text-label font-normal text-ink-muted">
        {t("past.title")}
      </h2>
      <ul className="flex flex-col gap-4">
        {cases.map((solved) => (
          <li key={solved.id} className="flex flex-col items-start gap-1">
            <p className="text-body-sm">{t("past.case", { number: solved.number, title: solved.title })}</p>
            <p className="font-type text-label text-ink-muted">{t(`ranks.${solved.rank}`)}</p>
            <Link
              href={`/cases/${solved.number}/certificate`}
              className="inline-flex min-h-10 items-center font-type text-label underline decoration-dotted decoration-2 underline-offset-[5px]"
            >
              {t("past.certificate")}
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
