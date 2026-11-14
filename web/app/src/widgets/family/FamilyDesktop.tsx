import Link from "next/link";
import { useTranslations } from "next-intl";
import { EveningBoxes, type Case } from "@/features/cases";
import { FamilyBoard, type Family } from "@/features/families";
import { NotebookPage, NotebookSpread, Wordmark } from "@/shared/components/notebook";
import { Board } from "./Board";
import { Tonight, TonightPending } from "./Tonight";

/** Design F3: tonight on the left page, the case board on the right. */
export function FamilyDesktop({ family, current }: { family: Family; current: Case | undefined }) {
  const t = useTranslations("widget.family");
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-center justify-between gap-6 border-b-[1.5px] border-rule-strong pb-4.5">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        {current ? <EveningBoxes episodes={current.episodes} /> : null}
        <span className="font-type text-label text-ink-muted">
          {t("detectives", { names: family.kids.map((kid) => kid.nickname).join(", ") })}
        </span>
      </header>
      <div className="mt-11">
        <NotebookSpread
          sideLabel={t("boardLabel")}
          main={current ? <Tonight current={current} large /> : <TonightPending large />}
          side={current && current.suspects.length > 0 ? <Board current={current} /> : <FamilyBoard family={family} />}
        />
      </div>
    </NotebookPage>
  );
}
