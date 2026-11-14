import Link from "next/link";
import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { EveningBoxes, inOpening, type Case } from "@/features/cases";
import { FamilyBoard, type FamilyState } from "@/features/families";
import { DetectivesTag, NotebookPage, NotebookSpread, PlansLink, Wordmark } from "@/shared/components/notebook";
import { Board } from "./Board";
import { NewFamily } from "./NewFamily";
import { Tonight, TonightPending, type Waiting } from "./Tonight";

/** Design F3: tonight on the left page, the case board on the right. */
export function FamilyDesktop({
  family,
  detectivesLabel,
  current,
  waiting,
  problem,
}: {
  family: FamilyState;
  detectivesLabel: string | undefined;
  current: Case | undefined;
  waiting: Waiting;
  /** Shown instead of tonight when the case did not load. */
  problem?: ReactNode;
}) {
  const t = useTranslations("widget.family");
  const detectives = family.kids.map((kid) => kid.nickname);
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-center justify-between gap-6 border-b-[1.5px] border-rule-strong pb-4.5">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        {current ? <EveningBoxes episodes={current.episodes} /> : null}
        {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        <PlansLink />
      </header>
      <div className="mt-11">
        <NotebookSpread
          sideLabel={t("boardLabel")}
          main={problem ?? (current ? <Tonight current={current} waiting={waiting} detectives={detectives} demoMode={family.demo_mode} large /> : <TonightPending waiting={waiting} detectives={detectives} large />)}
          side={current && current.suspects.length > 0 && !inOpening(current) ? <Board current={current} /> : <FamilyBoard family={family} />}
        />
      </div>
      <div className="mt-12">
        <NewFamily detectivesLabel={detectivesLabel} />
      </div>
    </NotebookPage>
  );
}
