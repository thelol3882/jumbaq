"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { SetupForm } from "@/features/families";
import { NotebookPage, Wordmark } from "@/shared/components/notebook";

/** The one-minute setup. One column on every screen, so no desktop variant. */
export function Setup() {
  const t = useTranslations("widget.setup");
  const router = useRouter();
  return (
    <NotebookPage>
      <Link href="/" className="self-start">
        <Wordmark text={t("wordmark")} size="sm" />
      </Link>
      <h1 className="mt-6 text-title">{t("title")}</h1>
      <p className="mt-2 font-type text-case font-normal text-ink-muted">{t("subtitle")}</p>
      <div className="mt-8">
        <SetupForm onCreated={() => router.push("/family")} />
      </div>
    </NotebookPage>
  );
}
