import type { Case } from "@/features/cases";
import { AnswerForm, DecodeParentNote, EpisodeResultView, ParentNote, StoryText } from "@/features/episodes";
import { NotebookPage } from "@/shared/components/notebook";
import { AfterTheAnswer, EveningHeader, StepMain, type ShownEpisode } from "./parts";

/** Designs D2 and D3: one page, read top to bottom. */
export function EveningMobile({
  current,
  episode,
  codeBreaker,
}: {
  current: Case;
  episode: ShownEpisode;
  codeBreaker?: string;
}) {
  const { step, result } = episode.content;
  return (
    <NotebookPage margin>
      <EveningHeader current={current} episode={episode} />
      <div className="mt-8 flex flex-col gap-9">
        {step === "done" && result ? (
          <>
            <EpisodeResultView result={result} />
            <AfterTheAnswer current={current} episode={episode} />
          </>
        ) : step === "decode" || step === "strike" ? (
          <>
            <StepMain current={current} episode={episode} codeBreaker={codeBreaker} inlineKey />
            {step === "decode" ? <DecodeParentNote /> : null}
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
