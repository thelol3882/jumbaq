import type { Case } from "@/features/cases";
import { AnswerForm, EpisodeResultView, ParentNote, StoryText } from "@/features/episodes";
import { NotebookPage } from "@/shared/components/notebook";
import { AfterTheAnswer, EveningHeader, type ShownEpisode } from "./parts";

/** Designs D2 and D3: one page, read top to bottom. */
export function EveningMobile({ current, episode }: { current: Case; episode: ShownEpisode }) {
  const played = episode.status === "played" && episode.content.result;
  return (
    <NotebookPage margin>
      <EveningHeader current={current} episode={episode} />
      <div className="mt-8 flex flex-col gap-9">
        {played && episode.content.result ? (
          <>
            <EpisodeResultView result={episode.content.result} />
            <AfterTheAnswer current={current} episode={episode} />
          </>
        ) : (
          <>
            <StoryText content={episode.content} />
            <ParentNote riddle={episode.content.riddle} />
            <AnswerForm episodeId={episode.id} content={episode.content} />
          </>
        )}
      </div>
    </NotebookPage>
  );
}
