"use client";

import { useTranslations } from "next-intl";
import { RiddleCard } from "@/shared/components/notebook";
import type { EpisodeContent } from "../types";

/** What the parent reads aloud: last time, the story, and the riddle on its card. Nothing to
 * click in here, so the kids look at the room, not at buttons. */
export function StoryText({ content, large = false }: { content: EpisodeContent; large?: boolean }) {
  const t = useTranslations("episodes");
  const aloud = large ? "text-[1.625rem] leading-[1.6]" : "text-aloud";
  return (
    <div className="flex flex-col">
      {content.recap ? (
        <p className="font-type text-case font-normal text-ink-muted">
          {t("lastTime")} {content.recap}
        </p>
      ) : null}
      <div className="relative mt-6 flex max-w-[34em] flex-col gap-4">
        <span
          aria-hidden="true"
          className="absolute top-1 -left-12 font-type text-label-sm text-aloud-label [writing-mode:vertical-rl] rotate-180"
        >
          {t("readAloud")}
        </span>
        {content.read_aloud.map((paragraph, index) => (
          <p key={index} className={`font-story ${aloud} text-aloud-fg`}>
            {paragraph}
          </p>
        ))}
      </div>
      <div className="mt-9 max-w-[40rem]">
        <RiddleCard label={t("riddle")} text={content.riddle.text} size={large ? "lg" : "md"} />
      </div>
    </div>
  );
}
