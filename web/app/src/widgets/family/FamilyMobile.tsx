import Link from "next/link";
import { useTranslations } from "next-intl";
import { EveningBoxes, type Case } from "@/features/cases";
import { FamilySummary, type Family } from "@/features/families";
import { NotebookPage, Wordmark } from "@/shared/components/notebook";
import { Board } from "./Board";
import { Tonight, TonightPending } from "./Tonight";

export function FamilyMobile({ family, current }: { family: Family; current: Case | undefined }) {
  const t = useTranslations("widget.family");
  return (
    <NotebookPage margin>
      <div className="flex items-center justify-between gap-4">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        {current ? <EveningBoxes episodes={current.episodes} /> : null}
      </div>
      <div className="mt-8 flex flex-col gap-9">
        {current ? <Tonight current={current} /> : <TonightPending />}
        {current && current.suspects.length > 0 ? <Board current={current} /> : <FamilySummary family={family} />}
      </div>
    </NotebookPage>
  );
}
