"use client";

import { useTranslations } from "next-intl";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, StampButton } from "@/shared/components/notebook";
import { useDecode } from "../hooks/useDecode";
import { numberCodeTable, shiftTable } from "../services/cipher";
import type { Decode } from "../types";
import { PickButton, ReadAloud } from "./ReadAloud";

/** The key to the cipher, for the grown-up to hold while the kids work. Nothing for the count level. */
export function CipherKey({ decode }: { decode: Decode }) {
  const t = useTranslations("episodes");
  if (decode.level === "count") return null;
  const cells =
    decode.level === "number_code"
      ? numberCodeTable(decode.key).map((r) => ({ id: r.letter, top: r.letter, bottom: String(r.number) }))
      : shiftTable(decode.key)
          .sort((a, b) => a.coded.localeCompare(b.coded))
          .map((r) => ({ id: r.coded, top: r.coded, bottom: r.plain }));
  return (
    <section aria-labelledby="cipher-key" className="flex flex-col gap-2.5">
      <h2 id="cipher-key" className="font-type text-label font-normal text-ink-muted">
        {decode.level === "number_code" ? t("decode.keyNumbers") : t("decode.keyShift")}
      </h2>
      <ul className="grid grid-cols-[repeat(auto-fill,minmax(3.25rem,1fr))] border-t-2 border-l-2 border-suspect-border bg-suspect-bg">
        {cells.map((c) => (
          <li
            key={c.id}
            className="flex flex-col items-center border-r-2 border-b-2 border-suspect-border py-1.5 font-type text-label"
          >
            <span className="font-bold text-suspect-fg">{c.top}</span>
            <span className="text-note-fg">{c.bottom}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** The grown-up's hint: the kids work on paper, the buttons only check. */
export function DecodeParentNote() {
  const t = useTranslations("episodes");
  return <HandNote>{t("decode.parentNote")}</HandNote>;
}

/**
 * The second step of an evening: crack the code. The read-aloud block comes first, then the code
 * and the picks below it. `inlineKey` puts the key table between the code and the picks (one column).
 */
export function DecodeStep({
  episodeId,
  decode,
  resolution,
  codeBreaker,
  inlineKey = false,
  large = false,
}: {
  episodeId: string;
  decode: Decode;
  resolution: string;
  codeBreaker?: string;
  inlineKey?: boolean;
  large?: boolean;
}) {
  const t = useTranslations("episodes");
  const errorMessage = useApiErrorMessage();
  const { pick, sending, error } = useDecode(episodeId);
  const counting = decode.level === "count";

  return (
    <div className="flex flex-col gap-7">
      <ReadAloud large={large}>
        <p>{resolution}</p>
        {codeBreaker ? <p>{t("decode.codeBreaker", { name: codeBreaker })}</p> : null}
        {counting ? (
          <p>{t("decode.countIntro", { key: decode.key, count: decode.count ?? 0 })}</p>
        ) : (
          <>
            <p>{decode.level === "number_code" ? t("decode.numberIntro") : t("decode.shiftIntro")}</p>
            {decode.clue_with_gap ? <p className="italic">{decode.clue_with_gap}</p> : null}
          </>
        )}
      </ReadAloud>
      {decode.code ? (
        <p className="font-type text-[2rem] leading-[1.3] font-bold tracking-wider break-words text-ink">
          {decode.code}
        </p>
      ) : null}
      {inlineKey ? <CipherKey decode={decode} /> : null}
      {decode.attempts > 0 ? <HandNote>{t("decode.wrong")}</HandNote> : null}
      {counting ? (
        <StampButton disabled={sending} onClick={() => void pick(null)}>
          {t("decode.weDidIt")}
        </StampButton>
      ) : (
        <div className="flex max-w-[40rem] flex-col gap-3">
          <p className="font-type text-case">{t("decode.pickLabel")}</p>
          {decode.options.map((option) => (
            <PickButton key={option} disabled={sending} onClick={() => void pick(option)}>
              {option}
            </PickButton>
          ))}
        </div>
      )}
      {error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}
