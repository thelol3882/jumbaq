import Link from "next/link";
import { useTranslations } from "next-intl";
import { AccuseForm, EveningBoxes, EvidenceList } from "@/features/cases";
import { DetectivesTag, NotebookPage, NotebookSpread, PlansLink, Wordmark } from "@/shared/components/notebook";
import { CertificateAndNext, SolvedStory, type AccuseViewProps } from "./parts";

/** Design F6: the evidence to read aloud on the left, the pick on the right; then the win. */
export function AccuseDesktop({ current, solved, onSolved, detectivesLabel, certificate }: AccuseViewProps) {
  const t = useTranslations("widget.accuse");
  const isSolved = current.status === "solved";
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-center justify-between gap-6 border-b-[1.5px] border-rule-strong pb-4.5">
        <div className="flex flex-col items-start">
          <Link href="/family" aria-label={t("back")}>
            <Wordmark text={t("wordmark")} size="sm" />
          </Link>
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <EveningBoxes episodes={current.episodes} />
        <PlansLink />
      </header>
      <div className="mt-11">
        {isSolved ? (
          <NotebookSpread
            sideLabel={t("certificateLabel")}
            main={<SolvedStory current={current} solved={solved} large />}
            side={<CertificateAndNext current={current} certificate={certificate} />}
          />
        ) : (
          <NotebookSpread
            sideLabel={t("pickLabel")}
            main={
              <div className="flex flex-col">
                <h1 className="text-[3rem] leading-[1.1] font-bold">{t("title")}</h1>
                <p className="mt-3.5 max-w-[30em] text-[1.5rem] leading-[1.5]">{t("intro")}</p>
                <p className="mt-8 mb-3 font-type text-label text-ink-muted">{t("evidence")}</p>
                <EvidenceList clues={current.clues} large />
              </div>
            }
            side={<AccuseForm current={current} onSolved={onSolved} />}
          />
        )}
      </div>
    </NotebookPage>
  );
}
