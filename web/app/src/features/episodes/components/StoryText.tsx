"use client";

import { useTranslations } from "next-intl";
import { RiddleCard } from "@/shared/components/notebook";
import { ReadAloud } from "./ReadAloud";
import type { EpisodeContent } from "../types";

/** What the parent reads aloud: last time, the story, and the riddle on its card. Nothing to
 * click in here, so the kids look at the room, not at buttons. */
export function StoryText({
  content,
  first = false,
  large = false,
}: {
  content: EpisodeContent;
  /** Evening 1: its recap is a welcome, not what happened last time. */
  first?: boolean;
  large?: boolean;
}) {
  const t = useTranslations("episodes");
  return (
    <div className="flex flex-col">
      {content.recap ? (
        <p className="font-type text-case font-normal text-ink-muted">
          {first ? content.recap : t("lastTime", { recap: content.recap })}
        </p>
      ) : null}
      <div className="mt-6">
        <ReadAloud large={large}>
          {content.read_aloud.map((paragraph, index) => (
            <p key={index} className="text-aloud-fg">
              {paragraph}
            </p>
          ))}
        </ReadAloud>
      </div>
      <div className="mt-9 max-w-[40rem]">
        <RiddleCard label={t("riddle")} text={content.riddle.text} size={large ? "lg" : "md"} />
      </div>
    </div>
  );
}
