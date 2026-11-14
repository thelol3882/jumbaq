import Link from "next/link";
import { useTranslations } from "next-intl";
import {
  CaseFilePreview,
  SetupFields,
  SetupFormShell,
  SetupSubmit,
  type SetupFormState,
} from "@/features/families";
import { HandNote, KeyHint, NotebookPage, NotebookSpread, Wordmark } from "@/shared/components/notebook";
import { useModifierKey } from "@/shared/hooks/useShortcut";

/** Design F2: the questions on the left page, the case file filling in on the right, with the
 * stamp always in view. */
export function SetupDesktop({ form }: { form: SetupFormState }) {
  const t = useTranslations("widget.setup");
  const modifier = useModifierKey();
  return (
    <NotebookPage width="wide">
      <header className="flex flex-wrap items-baseline justify-between gap-6">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        <span className="font-type text-label text-ink-muted">{t("subtitle")}</span>
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
                <div className="flex flex-col gap-3">
                  <SetupSubmit form={form} />
                  <KeyHint keys={[modifier, "↵"]} label={t("shortcut")} />
                </div>
                <HandNote lead={t("note.lead")} className="-rotate-1 text-note-sm">
                  {t("note.text")}
                </HandNote>
              </div>
            }
          />
        </SetupFormShell>
      </div>
    </NotebookPage>
  );
}
