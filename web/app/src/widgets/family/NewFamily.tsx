import Link from "next/link";
import { useTranslations } from "next-intl";
import { HandNote } from "@/shared/components/notebook";

/** The way to start over: the setup, with a plain word about what this phone forgets. */
export function NewFamily({ detectivesLabel }: { detectivesLabel: string | undefined }) {
  const t = useTranslations("widget.family");
  return (
    <div className="flex flex-col items-start gap-1">
      <Link
        href="/setup"
        className="inline-flex min-h-12 items-center px-1 font-type text-case font-normal text-secondary-fg underline decoration-dotted decoration-2 underline-offset-[5px]"
      >
        {t("newFamily.link")}
      </Link>
      {detectivesLabel ? <HandNote className="text-note-sm">{t("newFamily.note", { names: detectivesLabel })}</HandNote> : null}
    </div>
  );
}
