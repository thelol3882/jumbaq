import { useTranslations } from "next-intl";
import type { Case } from "@/features/cases";
import { AnswerForm, EpisodeResultView, ParentNote, StoryText } from "@/features/episodes";
import { NotebookPage, NotebookSpread } from "@/shared/components/notebook";
import { AfterTheAnswer, EveningHeader, type ShownEpisode } from "./parts";

/** Designs F4 and F5: the story and the answer on the left, the parent's page on the right. */
export function EveningDesktop({ current, episode }: { current: Case; episode: ShownEpisode }) {
  const t = useTranslations("widget.evening");
  const played = episode.status === "played" && episode.content.result;
  return (
    <NotebookPage width="wide">
      <EveningHeader current={current} episode={episode} wide />
      <div className="mt-10">
        <NotebookSpread
          sideLabel={played ? t("boardLabel") : t("parentLabel")}
          main={
            <article className="relative pl-14">
              <span aria-hidden="true" className="absolute -top-10 -bottom-14 left-7.5 border-l-[1.5px] border-rule-margin" />
              {played && episode.content.result ? (
                <EpisodeResultView result={episode.content.result} large />
              ) : (
                <div className="flex flex-col gap-9">
                  <StoryText content={episode.content} large />
                  <AnswerForm episodeId={episode.id} content={episode.content} />
                </div>
              )}
            </article>
          }
          side={
            played ? (
              <AfterTheAnswer current={current} episode={episode} />
            ) : (
              <ParentNote riddle={episode.content.riddle} />
            )
          }
        />
      </div>
    </NotebookPage>
  );
}
