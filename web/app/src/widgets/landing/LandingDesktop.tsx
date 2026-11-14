import { useTranslations } from "next-intl";
import { DetectivesTag, HandNote, NotebookPage, NotebookSpread, PlansLink, RiddleCard, StampLink, Wordmark } from "@/shared/components/notebook";
import { ForReviewers, Headline, Steps, WelcomeCard, type Welcome } from "./parts";

/** Design F1: the story on the left page, a real page of a case on the right. */
export function LandingDesktop({ startHref, welcome }: { startHref: string; welcome: Welcome | undefined }) {
  const t = useTranslations("widget.landing");
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-center justify-between gap-6 font-type text-label text-ink-muted">
        <span>{t("volume")}</span>
        {welcome?.tag ? <DetectivesTag text={welcome.tag} /> : null}
        <span>{t("facts")}</span>
        <PlansLink />
      </header>
      <div className="mt-10">
        <NotebookSpread
          sideLabel={t("example.pageLabel")}
          main={
            <div className="flex flex-col">
              <h1 className="self-start">
                <Wordmark text={t("wordmark")} size="xl" />
              </h1>
              <HandNote className="mt-1 ml-48 -rotate-3">{t("meaning")}</HandNote>
              <div className="mt-10">
                <Headline large />
              </div>
              <div className="mt-9 max-w-xl">
                <Steps large />
              </div>
              {welcome ? (
                <div className="mt-11 max-w-md">
                  <WelcomeCard welcome={welcome} />
                </div>
              ) : (
                <div className="mt-11 flex flex-wrap items-center gap-6">
                  <StampLink href={startHref} fit>
                    {t("start")}
                  </StampLink>
                  <HandNote>{t("free")}</HandNote>
                </div>
              )}
            </div>
          }
          side={
            <>
              <div className="pt-10" />
              <RiddleCard label={t("example.riddleLabel")} text={t("example.riddle")} />
              <HandNote lead={t("example.noteLead")} className="ml-3 -rotate-[1.5deg]">
                {t("example.note")}
              </HandNote>
            </>
          }
        />
      </div>
      <ForReviewers />
    </NotebookPage>
  );
}
