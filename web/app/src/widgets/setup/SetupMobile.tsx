import Link from "next/link";
import { useTranslations } from "next-intl";
import { SetupFields, SetupFormShell, SetupSubmit, type SetupFormState } from "@/features/families";
import { NotebookPage, Wordmark } from "@/shared/components/notebook";

export function SetupMobile({ form }: { form: SetupFormState }) {
  const t = useTranslations("widget.setup");
  return (
    <NotebookPage>
      <Link href="/" className="self-start">
        <Wordmark text={t("wordmark")} size="sm" />
      </Link>
      <h1 className="mt-6 text-title">{t("title")}</h1>
      <p className="mt-2 font-type text-case font-normal text-ink-muted">{t("subtitle")}</p>
      <div className="mt-8">
        <SetupFormShell form={form}>
          <div className="flex flex-col gap-9">
            <SetupFields form={form} />
            <SetupSubmit form={form} />
          </div>
        </SetupFormShell>
      </div>
    </NotebookPage>
  );
}
