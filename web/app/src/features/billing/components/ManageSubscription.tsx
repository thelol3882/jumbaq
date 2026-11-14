"use client";

import { useTranslations } from "next-intl";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { TypedButton } from "@/shared/components/notebook";
import { formatDay } from "@/shared/lib/dates";
import { usePortal } from "../hooks/usePortal";

/**
 * "Manage or cancel subscription": opens the Stripe portal. Show it only to a subscribed family.
 * After a cancel (`cancelsAt` set) the subscription is active until then, so it says so and the
 * link only manages, because the portal is also where the cancel is undone.
 */
export function ManageSubscription({ cancelsAt }: { cancelsAt?: string | null }) {
  const t = useTranslations("billing");
  const errorMessage = useApiErrorMessage();
  const { openPortal, redirecting, error } = usePortal();
  return (
    <div className="flex flex-col items-start gap-1">
      {cancelsAt ? (
        <p role="status" className="font-type text-case">
          {t("canceled", { date: formatDay(cancelsAt) })}
        </p>
      ) : null}
      <TypedButton disabled={redirecting} onClick={() => void openPortal()}>
        {cancelsAt ? t("manageCanceled") : t("manage")}
      </TypedButton>
      {error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}
