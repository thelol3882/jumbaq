"use client";

import { useTranslations } from "next-intl";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote } from "@/shared/components/notebook";
import { useStrike } from "../hooks/useStrike";
import type { Strike } from "../types";
import { ClueTag } from "./EpisodeResultView";
import { PickButton, ReadAloud } from "./ReadAloud";

/** The last step of an evening: the clue of tonight, then the kids pick a suspect. The suspects
 * come from the case, so the widget passes them in. The resolution was read on the decode step. */
export function StrikeStep({
  episodeId,
  number,
  strike,
  suspects,
  large = false,
}: {
  episodeId: string;
  number: number;
  strike: Strike;
  suspects: readonly { id: string; name: string }[];
  large?: boolean;
}) {
  const t = useTranslations("episodes");
  const errorMessage = useApiErrorMessage();
  const { pick, sending, error } = useStrike(episodeId);

  return (
    <div className="flex flex-col gap-7">
      <ClueTag number={number} text={strike.clue} />
      {strike.revealed_word && strike.decoded_word ? (
        <HandNote>{t("strike.revealed", { word: strike.decoded_word })}</HandNote>
      ) : null}
      <ReadAloud large={large}>
        <p>{strike.points_at ? t("strike.askPointsAt") : t("strike.askCrossOut")}</p>
      </ReadAloud>
      {strike.attempts > 0 ? <HandNote>{t("strike.wrong")}</HandNote> : null}
      <div className="flex max-w-[40rem] flex-col gap-3">
        {suspects.map((s) => (
          <PickButton key={s.id} disabled={sending} onClick={() => void pick(s.id)}>
            {s.name}
          </PickButton>
        ))}
      </div>
      {error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}
