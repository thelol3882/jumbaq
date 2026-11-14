"use client";

import { useTranslations } from "next-intl";
import { useEffect, useId, useRef, type ComponentProps, type ReactNode } from "react";
import { useFormErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, StampButton } from "@/shared/components/notebook";
import type { SetupFormState } from "../hooks/useSetupForm";
import { KID_COUNTS, OBJECT_PRESETS, ROOM_PRESETS } from "../services/presets";
import { hasErrors, isNicknameTaken, MAX_AGE, MAX_NICKNAME, MIN_AGE, MIN_OBJECTS } from "../services/setupForm";
import { ChoiceChips } from "./ChoiceChips";

const AGES = Array.from({ length: MAX_AGE - MIN_AGE + 1 }, (_, i) => MIN_AGE + i);

/** A tap target of 44 px. A picked one has a tick and a red pencil border; a disabled one is faint. */
function Chip({
  picked,
  square = false,
  className = "",
  children,
  ...props
}: Omit<ComponentProps<"button">, "type"> & { picked: boolean; square?: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={picked}
      className={
        "min-h-11 rounded-sm border bg-paper-card font-type text-case font-normal " +
        "disabled:border-dashed disabled:text-ink-faint disabled:line-through " +
        (square ? "min-w-11 px-2 " : "px-3 ") +
        (picked ? "border-accent-red text-accent-red " : "border-rule-card text-ink ") +
        className
      }
      {...props}
    >
      {picked ? (
        <span aria-hidden="true" className="mr-1 inline-block">
          {"✓"}
        </span>
      ) : null}
      {children}
    </button>
  );
}

/** The `<form>` around the fields and the submit, wherever the layout puts them. */
export function SetupFormShell({ form, children }: { form: SetupFormState; children: ReactNode }) {
  const ref = useRef<HTMLFormElement>(null);

  // After a stopped try, bring the first problem into view: on a wide screen the stamp is
  // far from the fields, and on a phone the problem can be above the fold.
  useEffect(() => {
    if (!form.blocked) return;
    const first = ref.current?.querySelector<HTMLElement>("[data-setup-error]");
    first?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [form.blocked]);

  return (
    <form
      ref={ref}
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
  const countId = useId();
  const { errors } = form;
  const legend = (key: "kids" | "rooms" | "objects", number: number) =>
    numbered ? t("numberedTitle", { number, title: t(`${key}.title`) }) : t(`${key}.title`);

  return (
    <div className="flex flex-col gap-9">
      <fieldset className="flex flex-col gap-4">
        <legend className="font-type text-case text-accent-red">{legend("kids", 1)}</legend>
        <HandNote className="text-note-sm">{t("kids.note")}</HandNote>
        <div role="group" aria-labelledby={countId} className="flex flex-col gap-2">
          <p id={countId} className="font-type text-label-sm text-ink-muted">
            {t("kids.count")}
          </p>
          <div className="flex gap-2">
            {KID_COUNTS.map((count) => (
              <Chip key={count} picked={form.draft.kids.length === count} onClick={() => form.setKidsCount(count)} square>
                {count}
              </Chip>
            ))}
          </div>
        </div>
        {form.draft.kids.map((kid, index) => {
          const error = errors.kid?.[kid.key];
          const errorId = `${kid.key}-error`;
          const nameId = `${kid.key}-name`;
          const ageId = `${kid.key}-age`;
          return (
            <div key={kid.key} className="flex flex-col gap-3 border-t border-dashed border-rule-card pt-4">
              <p className="font-type text-case font-bold">{t("kids.nickname", { number: index + 1 })}</p>
              <div role="group" aria-labelledby={nameId} className="flex flex-col gap-2">
                <p id={nameId} className="font-type text-label-sm text-ink-muted">
                  {t("kids.name")}
                </p>
                <div className="flex flex-wrap gap-2">
                  {form.nicknames.map((nickname) => {
                    const picked = !kid.custom && kid.nickname === nickname;
                    const taken = !picked && isNicknameTaken(form.draft.kids, kid.key, nickname);
                    return (
                      <Chip
                        key={nickname}
                        picked={picked}
                        disabled={taken}
                        onClick={() => form.setKid(kid.key, { nickname, custom: false })}
                      >
                        {nickname}
                        {taken ? <span className="sr-only"> ({t("kids.taken")})</span> : null}
                      </Chip>
                    );
                  })}
                  <Chip picked={kid.custom} onClick={() => form.setKid(kid.key, { nickname: "", custom: true })}>
                    {t("kids.own")}
                  </Chip>
                </div>
                {kid.custom ? (
                  <input
                    value={kid.nickname}
                    maxLength={MAX_NICKNAME}
                    autoComplete="off"
                    aria-label={t("kids.ownLabel", { number: index + 1 })}
                    placeholder={t("kids.ownPlaceholder")}
                    aria-invalid={error === "nicknameMissing" || error === "nicknameTooLong"}
                    aria-describedby={error ? errorId : undefined}
                    onChange={(e) => form.setKid(kid.key, { nickname: e.target.value })}
                    className="h-12 w-full rounded-sm border border-rule-card bg-paper-card px-3 font-story text-body placeholder:text-ink-faint"
                  />
                ) : null}
              </div>
              <div role="group" aria-labelledby={ageId} className="flex flex-col gap-2">
                <p id={ageId} className="font-type text-label-sm text-ink-muted">
                  {t("kids.age")}
                </p>
                <div className="flex flex-wrap gap-2">
                  {AGES.map((age) => (
                    <Chip
                      key={age}
                      picked={kid.age === String(age)}
                      onClick={() => form.setKid(kid.key, { age: String(age) })}
                      aria-describedby={error === "ageInvalid" ? errorId : undefined}
                      square
                    >
                      {age}
                    </Chip>
                  ))}
                </div>
              </div>
              {error ? (
                <p id={errorId} data-setup-error className="font-type text-label text-gentle-error-fg">
                  {t(`kids.errors.${error}`, { min: MIN_AGE, max: MAX_AGE })}
                </p>
              ) : null}
            </div>
          );
        })}
        {errors.kids ? (
          <p data-setup-error className="font-type text-label text-gentle-error-fg">{t("kids.errors.repeated")}</p>
        ) : null}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-type text-case text-accent-red">{legend("rooms", 2)}</legend>
        <HandNote className="text-note-sm">{t("rooms.note")}</HandNote>
        <ChoiceChips
          options={ROOM_PRESETS.map((key) => ({ value: key, label: t(`rooms.presets.${key}`) }))}
          selected={form.draft.rooms}
          onToggle={form.toggleRoom}
          addLink={t("rooms.addLink")}
          addLabel={t("rooms.addLabel")}
          addPlaceholder={t("rooms.addPlaceholder")}
          addButton={t("add")}
        />
        {errors.rooms ? (
          <p data-setup-error className="font-type text-label text-gentle-error-fg">{t(`rooms.errors.${errors.rooms}`)}</p>
        ) : null}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="font-type text-case text-accent-red">{legend("objects", 3)}</legend>
        <HandNote className="text-note-sm">{t("objects.note", { min: MIN_OBJECTS })}</HandNote>
        <ChoiceChips
          options={OBJECT_PRESETS.map((key) => ({ value: key, label: t(`objects.presets.${key}`) }))}
          selected={form.draft.objects}
          onToggle={form.toggleObject}
          addLink={t("objects.addLink")}
          addLabel={t("objects.addLabel")}
          addPlaceholder={t("objects.addPlaceholder")}
          addButton={t("add")}
          showFirst={8}
          showMoreLabel={(count) => t("showMore", { count })}
        />
        {errors.objects ? (
          <p data-setup-error className="font-type text-label text-gentle-error-fg">
            {t(`objects.errors.${errors.objects}`, { min: MIN_OBJECTS, count: form.draft.objects.length })}
          </p>
        ) : null}
      </fieldset>
    </div>
  );
}

/** The error of the last try and the stamp that opens the case file. With `sticky` the stamp stays
 * at the bottom of the phone screen; the errors stay in the flow above it, never under it. */
export function SetupSubmit({ form, sticky = false }: { form: SetupFormState; sticky?: boolean }) {
  const t = useTranslations("families");
  const formError = useFormErrorMessage();
  const messages =
    hasErrors(form.errors) || form.error ? (
      <div className="flex flex-col gap-3">
        {hasErrors(form.errors) ? (
          <p role="alert" className="font-type text-label text-gentle-error-fg">
            {t("checkAnswers")}
          </p>
        ) : null}
        {form.error ? (
          <p role="alert" className="border border-gentle-error-border bg-gentle-error-bg p-3 font-type text-label text-gentle-error-fg">
            {formError(form.error)}
          </p>
        ) : null}
      </div>
    ) : null;
  const stamp = (
    <StampButton type="submit" disabled={form.saving}>
      {form.saving ? t("submitting") : t("submit")}
    </StampButton>
  );

  if (!sticky) {
    return (
      <div className="flex flex-col gap-3">
        {messages}
        {stamp}
      </div>
    );
  }
  // A fragment, so the sticky bar is a child of the long column and can stick along all of it.
  return (
    <>
      {messages}
      <div className="sticky bottom-0 z-10 bg-paper pt-3 pb-[max(1rem,env(safe-area-inset-bottom))]">{stamp}</div>
    </>
  );
}
