import type { Case } from "@/features/cases";
import { AnswerForm, DecodeParentNote, EpisodeResultView, ParentNote, StoryText } from "@/features/episodes";
import { NotebookPage } from "@/shared/components/notebook";
import { AfterTheAnswer, EveningDemo, EveningHeader, StepMain, type ShownEpisode } from "./parts";
import { useStepScroll } from "./useStepScroll";

/** Designs D2 and D3: one page, read top to bottom. */
export function EveningMobile({
  current,
  episode,
  codeBreaker,
  detectivesLabel,
  demoMode,
}: {
  current: Case;
  episode: ShownEpisode;
  codeBreaker?: string;
  detectivesLabel: string | undefined;
  demoMode: boolean;
}) {
  const { step, result } = episode.content;
  const main = useStepScroll<HTMLDivElement>(step);
  return (
    <NotebookPage margin>
      <EveningHeader current={current} episode={episode} detectivesLabel={detectivesLabel} />
      <div ref={main} className="mt-8 flex scroll-mt-4 flex-col gap-9">
        {step === "done" && result ? (
          <>
            <EpisodeResultView result={result} last={episode.number === current.episodes.length} />
            <AfterTheAnswer current={current} episode={episode} />
          </>
        ) : step === "decode" || step === "strike" ? (
          <>
            <StepMain current={current} episode={episode} codeBreaker={codeBreaker} inlineKey />
            {step === "decode" ? <DecodeParentNote /> : null}
          </>
        ) : (
          <>
            <StoryText content={episode.content} first={episode.number === 1} />
            <ParentNote riddle={episode.content.riddle} />
            <AnswerForm episodeId={episode.id} content={episode.content} />
          </>
        )}
        <EveningDemo episode={episode} demoMode={demoMode} />
      </div>
    </NotebookPage>
  );
}
