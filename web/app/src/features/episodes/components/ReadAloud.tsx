"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

/** The read-aloud column with its red margin label. Nothing to click inside it. */
export function ReadAloud({ children, large = false }: { children: ReactNode; large?: boolean }) {
  const t = useTranslations("episodes");
  const aloud = large ? "text-aloud-lg" : "text-aloud";
  return (
    <div className="relative max-w-[34em]">
      <span
        aria-hidden="true"
        className="absolute top-1 -left-12 rotate-180 font-type text-label-sm text-aloud-label [writing-mode:vertical-rl]"
      >
        {t("readAloud")}
      </span>
      <div className={`flex flex-col gap-4 font-story ${aloud} text-aloud-fg`}>{children}</div>
    </div>
  );
}

/** A big touch target for one pick, in typewriter type. */
export function PickButton({
  children,
  disabled,
  onClick,
}: {
  children: ReactNode;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="min-h-14 w-full rounded-sm border-2 border-suspect-border bg-suspect-bg px-4 py-2 text-left font-type text-pick text-suspect-fg active:bg-secondary-bg disabled:cursor-progress disabled:opacity-70"
    >
      {children}
    </button>
  );
}
