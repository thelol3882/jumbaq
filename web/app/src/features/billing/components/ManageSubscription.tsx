"use client";

import { useTranslations } from "next-intl";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { TypedButton } from "@/shared/components/notebook";
import { usePortal } from "../hooks/usePortal";

/** "Manage or cancel subscription": opens the Stripe portal. Show it only to a subscribed family. */
export function ManageSubscription() {
  const t = useTranslations("billing");
  const errorMessage = useApiErrorMessage();
  const { openPortal, redirecting, error } = usePortal();
  return (
    <div className="flex flex-col items-start gap-1">
      <TypedButton disabled={redirecting} onClick={() => void openPortal()}>
        {t("manage")}
      </TypedButton>
      {error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}
