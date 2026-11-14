import Link from "next/link";
import { useTranslations } from "next-intl";
import { FamilyBoard, type Family } from "@/features/families";
import { HandNote, NotebookPage, NotebookSpread, Wordmark } from "@/shared/components/notebook";

/** Design F3: tonight on the left page, the case board on the right. */
export function FamilyDesktop({ family }: { family: Family }) {
  const t = useTranslations("widget.family");
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-center justify-between gap-6 border-b-[1.5px] border-rule-strong pb-4.5">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        <span className="font-type text-case">{t("eyebrow")}</span>
        <span className="font-type text-label-sm text-ink-muted">
          {family.kids.map((kid) => kid.nickname).join(" · ")}
        </span>
      </header>
      <div className="mt-11">
        <NotebookSpread
          sideLabel={t("boardLabel")}
          main={
            <div className="flex flex-col">
              <p className="font-type text-case text-accent-red">{t("tonight")}</p>
              <h1 className="mt-2.5 max-w-2xl text-[2.875rem] leading-[1.12] font-bold">{t("title")}</h1>
              <svg aria-hidden="true" width="300" height="12" viewBox="0 0 200 10" className="mt-1">
                <path d="M2 5 C 50 8, 120 2, 198 6" stroke="var(--color-accent-red)" strokeWidth="2" fill="none" strokeLinecap="round" />
              </svg>
              <HandNote lead={t("next.lead")} className="mt-9 max-w-xl -rotate-1">
                {t("next.text")}
              </HandNote>
            </div>
          }
          side={<FamilyBoard family={family} />}
        />
      </div>
    </NotebookPage>
  );
}
