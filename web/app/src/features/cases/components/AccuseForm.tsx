"use client";

import { useTranslations } from "next-intl";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, StampButton } from "@/shared/components/notebook";
import { useAccusation } from "../hooks/useAccusation";
import type { Accusation, Case } from "../types";

// The hand-drawn picks sit a little crooked on purpose.
const TILT = ["-rotate-[0.6deg] mr-4.5", "rotate-[0.8deg] ml-2.5", "-rotate-[0.3deg] mr-1.5"] as const;

/** Pick one suspect and accuse. `onSolved` gets the reveal, which only this answer carries. */
export function AccuseForm({ current, onSolved }: { current: Case; onSolved: (result: Accusation) => void }) {
  const t = useTranslations("cases");
  const errorMessage = useApiErrorMessage();
  const form = useAccusation(current.id);
  const pickedName = current.suspects.find((s) => s.id === form.picked)?.name;

  return (
    <form
      onSubmit={async (e) => {
        e.preventDefault();
        const result = await form.submit();
        if (result?.correct) onSolved(result);
      }}
      className="flex flex-col gap-5"
    >
      <fieldset className="m-0 border-0 p-0">
        <legend className="font-type text-case">{t("accuse.pickOne")}</legend>
        <div className="mt-3 flex flex-col gap-3.5">
          {current.suspects.map((s, index) => (
            <label
              key={s.id}
              className={`relative flex min-h-18 cursor-pointer items-center gap-4 border-2 bg-suspect-bg px-4.5 ${TILT[index % TILT.length]} ${
                form.picked === s.id ? "border-accent-red" : "border-ink"
              }`}
            >
              <input
                type="radio"
                name="suspect"
                aria-label={s.name}
                value={s.id}
                checked={form.picked === s.id}
                onChange={() => form.pick(s.id)}
                className="size-6.5 shrink-0 appearance-none border-2 border-ink bg-suspect-bg checked:bg-accent-red checked:shadow-[inset_0_0_0_4px_var(--color-suspect-bg)]"
              />
              <span className="font-type text-pick">{s.name}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {form.wrongPick ? (
        <p role="status" className="border border-gentle-error-border bg-gentle-error-bg p-3 font-hand text-note text-gentle-error-fg">
          {t("accuse.wrong")}
        </p>
      ) : null}
      {form.error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(form.error)}
        </p>
      ) : null}

      <StampButton type="submit" disabled={!form.picked || form.accusing}>
        {pickedName ? t("accuse.submit", { name: pickedName }) : t("accuse.submitEmpty")}
      </StampButton>
      <HandNote lead={t("accuse.noteLead")} className="-rotate-1 text-note-sm">
        {t("accuse.note")}
      </HandNote>
    </form>
  );
}
