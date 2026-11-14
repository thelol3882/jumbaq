"use client";

import { useRouter } from "next/navigation";
import { useSetupForm } from "@/features/families";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { useSubmitShortcut } from "@/shared/hooks/useShortcut";
import { SetupDesktop } from "./SetupDesktop";
import { SetupMobile } from "./SetupMobile";

/** The one-minute setup. The form state lives here, so a resize keeps what was typed. */
export function Setup() {
  const router = useRouter();
  const form = useSetupForm(() => router.push("/family"));
  const isMobile = useIsMobile();
  useSubmitShortcut(() => void form.submit(), !isMobile && !form.saving);

  return isMobile ? <SetupMobile form={form} /> : <SetupDesktop form={form} />;
}
