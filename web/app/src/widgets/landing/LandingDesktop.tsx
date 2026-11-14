import { useTranslations } from "next-intl";
import { HandNote, NotebookPage, NotebookSpread, RiddleCard, StampLink, Wordmark } from "@/shared/components/notebook";
import { ExampleExhibit, Headline, Steps } from "./parts";

/** Design F1: the story on the left page, a real page of a case on the right. */
export function LandingDesktop({ startHref }: { startHref: string }) {
  const t = useTranslations("widget.landing");
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-center justify-between gap-6 font-type text-label text-ink-muted">
        <span>{t("volume")}</span>
        <span>{t("facts")}</span>
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
              <div className="mt-11 flex flex-wrap items-center gap-6">
                <StampLink href={startHref} fit>
                  {t("start")}
                </StampLink>
                <HandNote>{t("free")}</HandNote>
              </div>
            </div>
          }
          side={
            <>
              <p className="pt-3 font-type text-label text-ink-muted">{t("example.pageLabel")}</p>
              <RiddleCard label={t("example.riddleLabel")} text={t("example.riddle")} />
              <HandNote lead={t("example.noteLead")} className="ml-3 -rotate-[1.5deg]">
                {t("example.note")}
              </HandNote>
              <div className="self-end">
                <ExampleExhibit />
              </div>
            </>
          }
        />
      </div>
    </NotebookPage>
  );
}
