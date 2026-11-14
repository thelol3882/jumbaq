"use client";

import { useTranslations } from "next-intl";
import { HandNote, TypedButton, WritingSteps } from "@/shared/components/notebook";
import { writingStage, writingSteps, type WritingStepKey } from "../services/writing";
import type { Case } from "../types";

/** What the worker is writing now, how long it takes, and a calm way out when it is slow. */
export function WritingProgress({
  current,
  slow,
  onCheck,
}: {
  current: Case | undefined;
  slow: boolean;
  onCheck: () => void;
}) {
  const t = useTranslations("cases");
  const stage = writingStage(current);
  const evening = stage.kind === "evening" ? stage.number : 1;
  const labels: Record<WritingStepKey, string> = {
    file: t("writing.steps.file"),
    plan: t("writing.steps.plan"),
    evening: t("writing.steps.evening", { number: evening }),
    evidence: t("writing.steps.evidence"),
  };
  const steps = writingSteps(stage).map((s) => ({ ...s, label: labels[s.key] }));
  const isNew = stage.kind !== "closing" && !(stage.kind === "evening" && stage.number > 1);

  return (
    <div className="flex flex-col gap-6">
      <WritingSteps steps={steps} stateLabels={{ done: t("writing.state.done"), now: t("writing.state.now"), todo: t("writing.state.todo") }} />
      {slow ? (
        <div className="flex flex-col items-start gap-2">
          <HandNote lead={t("writing.slow.lead")}>{t("writing.slow.text")}</HandNote>
          <TypedButton onClick={onCheck}>{t("writing.slow.check")}</TypedButton>
        </div>
      ) : (
        <HandNote lead={t("writing.expect.lead")}>{isNew ? t("writing.expect.case") : t("writing.expect.evening")}</HandNote>
      )}
    </div>
  );
}
