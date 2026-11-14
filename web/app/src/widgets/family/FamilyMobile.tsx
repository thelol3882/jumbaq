import Link from "next/link";
import { useTranslations } from "next-intl";
import { FamilySummary, type Family } from "@/features/families";
import { HandNote, NotebookPage, Wordmark } from "@/shared/components/notebook";

export function FamilyMobile({ family }: { family: Family }) {
  const t = useTranslations("widget.family");
  return (
    <NotebookPage margin>
      <Link href="/" className="self-start">
        <Wordmark text={t("wordmark")} size="sm" />
      </Link>
      <div className="mt-8 flex flex-col gap-8">
        <div>
          <p className="font-type text-case">{t("eyebrow")}</p>
          <h1 className="mt-2 text-title">{t("title")}</h1>
        </div>
        <FamilySummary family={family} />
        <HandNote lead={t("next.lead")}>{t("next.text")}</HandNote>
      </div>
    </NotebookPage>
  );
}
