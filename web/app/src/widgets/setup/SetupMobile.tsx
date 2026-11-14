import Link from "next/link";
import { useTranslations } from "next-intl";
import { SetupFields, SetupFormShell, SetupSubmit, type SetupFormState } from "@/features/families";
import { NotebookPage, PlansLink, Wordmark } from "@/shared/components/notebook";

export function SetupMobile({ form }: { form: SetupFormState }) {
  const t = useTranslations("widget.setup");
  return (
    <NotebookPage>
      <div className="flex items-center justify-between gap-4">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        <PlansLink />
      </div>
      <h1 className="mt-6 text-title">{t("title")}</h1>
      <p className="mt-2 font-type text-case font-normal text-ink-muted">{t("subtitle")}</p>
      <div className="mt-8">
        <SetupFormShell form={form}>
          <div className="flex flex-col gap-9">
            <SetupFields form={form} />
            <SetupSubmit form={form} sticky />
          </div>
        </SetupFormShell>
      </div>
    </NotebookPage>
  );
}
