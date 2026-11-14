import Link from "next/link";
import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { EveningBoxes, inOpening, type Case } from "@/features/cases";
import { FamilySummary, type FamilyState } from "@/features/families";
import { NotebookPage, Wordmark } from "@/shared/components/notebook";
import { Board } from "./Board";
import { Tonight, TonightPending, type Waiting } from "./Tonight";

export function FamilyMobile({
  family,
  current,
  waiting,
  problem,
}: {
  family: FamilyState;
  current: Case | undefined;
  waiting: Waiting;
  /** Shown instead of tonight when the case did not load. */
  problem?: ReactNode;
}) {
  const t = useTranslations("widget.family");
  const detectives = family.kids.map((kid) => kid.nickname);
  return (
    <NotebookPage margin>
      <div className="flex items-center justify-between gap-4">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        {current ? <EveningBoxes episodes={current.episodes} /> : null}
      </div>
      <div className="mt-8 flex flex-col gap-9">
        {problem ?? (current ? <Tonight current={current} waiting={waiting} detectives={detectives} demoMode={family.demo_mode} /> : <TonightPending waiting={waiting} detectives={detectives} />)}
        {current && current.suspects.length > 0 && !inOpening(current) ? <Board current={current} /> : <FamilySummary family={family} />}
      </div>
    </NotebookPage>
  );
}
