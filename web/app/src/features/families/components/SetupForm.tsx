"use client";

import { useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { useFormErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, StampButton } from "@/shared/components/notebook";
import type { SetupFormState } from "../hooks/useSetupForm";
import { MAX_AGE, MIN_AGE, MIN_OBJECTS } from "../services/setupForm";
import { OBJECT_PRESETS, ROOM_PRESETS } from "../services/presets";
import { ChoiceChips } from "./ChoiceChips";

/** The `<form>` around the fields and the submit, wherever the layout puts them. */
export function SetupFormShell({ form, children }: { form: SetupFormState; children: ReactNode }) {
  return (
    <form
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        void form.submit();
      }}
    >
      {children}
    </form>
  );
}

/** The three questions of the setup: detectives, scene, evidence. */
export function SetupFields({ form, numbered = false }: { form: SetupFormState; numbered?: boolean }) {
  const t = useTranslations("families");
  const { errors } = form;
  const legend = (key: "kids" | "rooms" | "objects", number: number) =>
    numbered ? t("numberedTitle", { number, title: t(`${key}.title`) }) : t(`${key}.title`);

  return (
    <div className="flex flex-col gap-9">
      <fieldset className="flex flex-col gap-3">
        <legend className="font-type text-case text-accent-red">{legend("kids", 1)}</legend>
        <HandNote className="text-note-sm">{t("kids.note")}</HandNote>
        {form.draft.kids.map((kid, index) => {
          const error = errors.kid?.[kid.key];
          const errorId = `${kid.key}-error`;
          return (
            <div key={kid.key} className="flex flex-col gap-1">
              <div className="flex items-end gap-2">
                <label className="min-w-0 flex-1">
                  <span className="font-type text-label-sm text-ink-muted">
                    {t("kids.nickname", { number: index + 1 })}
                  </span>
                  <input
                    value={kid.nickname}
                    maxLength={40}
                    autoComplete="off"
                    aria-invalid={error === "nicknameMissing" || error === "nicknameTooLong"}
                    aria-describedby={error ? errorId : undefined}
                    onChange={(e) => form.setKid(kid.key, { nickname: e.target.value })}
                    className="mt-1 h-12 w-full rounded-sm border border-rule-card bg-paper-card px-3 font-story text-body"
                  />
                </label>
                <label className="w-20">
                  <span className="font-type text-label-sm text-ink-muted">{t("kids.age")}</span>
                  <input
                    value={kid.age}
                    inputMode="numeric"
                    maxLength={2}
                    aria-invalid={error === "ageInvalid"}
                    aria-describedby={error ? errorId : undefined}
                    onChange={(e) => form.setKid(kid.key, { age: e.target.value })}
                    className="mt-1 h-12 w-full rounded-sm border border-rule-card bg-paper-card px-3 font-story text-body"
                  />
                </label>
                {form.draft.kids.length > 1 ? (
                  <button
                    type="button"
                    onClick={() => form.removeKid(kid.key)}
                    aria-label={t("kids.remove", { number: index + 1 })}
                    className="h-12 shrink-0 px-1 font-type text-label text-ink-muted underline decoration-dotted decoration-2 underline-offset-[5px]"
                  >
                    {t("kids.removeShort")}
                  </button>
                ) : null}
              </div>
              {error ? (
                <p id={errorId} className="font-type text-label text-gentle-error-fg">
                  {t(`kids.errors.${error}`, { min: MIN_AGE, max: MAX_AGE })}
                </p>
              ) : null}
            </div>
          );
        })}
        {errors.kids ? (
          <p className="font-type text-label text-gentle-error-fg">{t("kids.errors.repeated")}</p>
        ) : null}
        {form.canAddKid ? (
          <button
            type="button"
            onClick={form.addKid}
            className="self-start font-type text-case font-normal underline decoration-dotted decoration-2 underline-offset-[5px]"
          >
            {t("kids.add")}
          </button>
        ) : null}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-type text-case text-accent-red">{legend("rooms", 2)}</legend>
        <HandNote className="text-note-sm">{t("rooms.note")}</HandNote>
        <ChoiceChips
          options={ROOM_PRESETS.map((key) => ({ value: key, label: t(`rooms.presets.${key}`) }))}
          selected={form.draft.rooms}
          onToggle={form.toggleRoom}
          addLabel={t("rooms.addLabel")}
          addPlaceholder={t("rooms.addPlaceholder")}
          addButton={t("add")}
        />
        {errors.rooms ? (
          <p className="font-type text-label text-gentle-error-fg">{t(`rooms.errors.${errors.rooms}`)}</p>
        ) : null}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-type text-case text-accent-red">{legend("objects", 3)}</legend>
        <HandNote className="text-note-sm">{t("objects.note", { min: MIN_OBJECTS })}</HandNote>
        <ChoiceChips
          options={OBJECT_PRESETS.map((key) => ({ value: key, label: t(`objects.presets.${key}`) }))}
          selected={form.draft.objects}
          onToggle={form.toggleObject}
          addLabel={t("objects.addLabel")}
          addPlaceholder={t("objects.addPlaceholder")}
          addButton={t("add")}
          showFirst={8}
          showMoreLabel={(count) => t("showMore", { count })}
        />
        {errors.objects ? (
          <p className="font-type text-label text-gentle-error-fg">
            {t(`objects.errors.${errors.objects}`, { min: MIN_OBJECTS, count: form.draft.objects.length })}
          </p>
        ) : null}
      </fieldset>
    </div>
  );
}

/** The error of the last try and the stamp that opens the case file. */
export function SetupSubmit({ form }: { form: SetupFormState }) {
  const t = useTranslations("families");
  const formError = useFormErrorMessage();
  return (
    <div className="flex flex-col gap-3">
      {form.error ? (
        <p role="alert" className="border border-gentle-error-border bg-gentle-error-bg p-3 font-type text-label text-gentle-error-fg">
          {formError(form.error)}
        </p>
      ) : null}
      <StampButton type="submit" disabled={form.saving}>
        {form.saving ? t("submitting") : t("submit")}
      </StampButton>
    </div>
  );
}
