import Link from "next/link";
import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { ManageSubscription } from "@/features/billing";
import { EveningBoxes, inOpening, type Case } from "@/features/cases";
import { FamilySummary, type FamilyState } from "@/features/families";
import { DetectivesTag, NotebookPage, PlansLink, Wordmark } from "@/shared/components/notebook";
import { Board } from "./Board";
import { NewFamily } from "./NewFamily";
import { Tonight, TonightPending, type Waiting } from "./Tonight";

export function FamilyMobile({
  family,
  detectivesLabel,
  current,
  waiting,
  problem,
  subscribed,
  cancelsAt,
}: {
  family: FamilyState;
  detectivesLabel: string | undefined;
  current: Case | undefined;
  waiting: Waiting;
  /** Shown instead of tonight when the case did not load. */
  problem?: ReactNode;
  /** The family has a subscription it can manage. */
  subscribed: boolean;
  /** When a canceled subscription ends, else null. */
  cancelsAt: string | null;
}) {
  const t = useTranslations("widget.family");
  const detectives = family.kids.map((kid) => kid.nickname);
  return (
    <NotebookPage margin>
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3">
        <div className="flex flex-col items-start">
          <Link href="/">
            <Wordmark text={t("wordmark")} size="sm" />
          </Link>
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <PlansLink />
        {/* Five boxes are about 200px: on their own row below, so Plans never leaves the screen. */}
        {current ? (
          <div className="order-last basis-full">
            <EveningBoxes episodes={current.episodes} />
          </div>
        ) : null}
      </div>
      <div className="mt-8 flex flex-col gap-9">
        {problem ?? (current ? <Tonight current={current} waiting={waiting} detectives={detectives} demoMode={family.demo_mode} /> : <TonightPending waiting={waiting} detectives={detectives} />)}
        {current && current.suspects.length > 0 && !inOpening(current) ? <Board current={current} /> : <FamilySummary family={family} />}
        {subscribed ? <ManageSubscription cancelsAt={cancelsAt} /> : null}
        <NewFamily detectivesLabel={detectivesLabel} />
      </div>
    </NotebookPage>
  );
}
