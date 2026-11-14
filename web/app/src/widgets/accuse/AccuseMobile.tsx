import Link from "next/link";
import { useTranslations } from "next-intl";
import { AccuseForm, EvidenceList } from "@/features/cases";
import { DetectivesTag, NotebookPage, PlansLink, Wordmark } from "@/shared/components/notebook";
import { CertificateAndNext, SolvedStory, type AccuseViewProps } from "./parts";

/** Design D4: evidence, the pick and the stamp; after the right pick, the win and the certificate. */
export function AccuseMobile({ current, solved, onSolved, detectivesLabel, certificate, subscription }: AccuseViewProps) {
  const t = useTranslations("widget.accuse");
  return (
    <NotebookPage margin>
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col items-start">
          <Link href="/family" aria-label={t("back")}>
            <Wordmark text={t("wordmark")} size="sm" />
          </Link>
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <PlansLink />
      </div>
      <div className="mt-8 flex flex-col gap-8">
        {current.status === "solved" ? (
          <>
            <SolvedStory current={current} solved={solved} />
            <CertificateAndNext current={current} certificate={certificate} subscription={subscription} />
          </>
        ) : (
          <>
            <div>
              <h1 className="text-display">{t("title")}</h1>
              <p className="mt-3 text-body">{t("intro")}</p>
            </div>
            <div>
              <p className="mb-2 font-type text-label text-ink-muted">{t("evidence")}</p>
              <EvidenceList clues={current.clues} />
            </div>
            <AccuseForm current={current} onSolved={onSolved} />
          </>
        )}
      </div>
    </NotebookPage>
  );
}
