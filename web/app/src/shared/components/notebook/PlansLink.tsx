"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

/** The link to the price and the subscription, in the header of every screen. */
export function PlansLink() {
  const t = useTranslations("common");
  return (
    <Link
      href="/plans"
      className="inline-flex min-h-10 items-center font-type text-label text-ink-muted underline decoration-dotted decoration-2 underline-offset-[5px]"
    >
      {t("nav.plans")}
    </Link>
  );
}
