import Link from "next/link";
import { useTranslations } from "next-intl";
import {
  CaseFilePreview,
  SetupFields,
  SetupFormShell,
  SetupSubmit,
  type SetupFormState,
} from "@/features/families";
import { HandNote, NotebookPage, NotebookSpread, PlansLink, Wordmark } from "@/shared/components/notebook";

/** Design F2: the questions on the left page, the case file filling in on the right, with the
 * stamp always in view. */
export function SetupDesktop({ form }: { form: SetupFormState }) {
  const t = useTranslations("widget.setup");
  return (
    <NotebookPage width="wide">
      <header className="flex items-center justify-between gap-6">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        <PlansLink />
      </header>
      <div className="mt-9">
        <SetupFormShell form={form}>
          <NotebookSpread
            sideLabel={t("previewLabel")}
            main={
              <div className="flex flex-col gap-11">
                <div>
                  <h1 className="text-[2.5rem] leading-[1.12] font-bold">{t("title")}</h1>
                  <HandNote className="mt-2">{t("intro")}</HandNote>
                </div>
                <SetupFields form={form} numbered />
              </div>
            }
            side={
              <div className="sticky top-6 flex flex-col gap-7 pt-1.5">
                <p className="font-type text-label text-ink-muted">{t("previewLabel")}</p>
                <CaseFilePreview draft={form.draft} />
                <SetupSubmit form={form} />
              </div>
            }
          />
        </SetupFormShell>
      </div>
    </NotebookPage>
  );
}
