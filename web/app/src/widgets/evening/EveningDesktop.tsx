import { useTranslations } from "next-intl";
import { SuspectTable, type Case } from "@/features/cases";
import {
  AnswerForm,
  CipherKey,
  DecodeParentNote,
  EpisodeResultView,
  ParentNote,
  StoryText,
} from "@/features/episodes";
import { NotebookPage, NotebookSpread } from "@/shared/components/notebook";
import { AfterTheAnswer, EveningDemo, EveningHeader, StepMain, type ShownEpisode } from "./parts";
import { useStepScroll } from "./useStepScroll";

/** Designs F4 and F5: the story and the steps on the left, the parent's page on the right. */
export function EveningDesktop({
  current,
  episode,
  codeBreaker,
}: {
  current: Case;
  episode: ShownEpisode;
  codeBreaker?: string;
}) {
  const t = useTranslations("widget.evening");
  const { step, result, decode } = episode.content;
  const done = step === "done" && result;
  const main = useStepScroll<HTMLElement>(step);
  return (
    <NotebookPage width="wide">
      <EveningHeader current={current} episode={episode} wide />
      <div className="mt-10">
        <NotebookSpread
          sideLabel={done ? t("boardLabel") : t("parentLabel")}
          main={
            <article ref={main} className="relative scroll-mt-4 pl-14">
              <span aria-hidden="true" className="absolute -top-10 -bottom-14 left-7.5 border-l-[1.5px] border-rule-margin" />
              {done ? (
                <EpisodeResultView result={result} last={episode.number === current.episodes.length} large />
              ) : step === "decode" || step === "strike" ? (
                <StepMain current={current} episode={episode} codeBreaker={codeBreaker} large />
              ) : (
                <div className="flex flex-col gap-9">
                  <StoryText content={episode.content} first={episode.number === 1} large />
                  <AnswerForm episodeId={episode.id} content={episode.content} />
                </div>
              )}
            </article>
          }
          side={
            done ? (
              <AfterTheAnswer current={current} episode={episode} />
            ) : step === "decode" ? (
              <>
                {decode ? <CipherKey decode={decode} /> : null}
                <DecodeParentNote />
              </>
            ) : step === "strike" ? (
              <section aria-labelledby="evening-suspects">
                <h2 id="evening-suspects" className="mb-2.5 font-type text-label font-normal text-ink-muted">
                  {t("suspects")}
                </h2>
                <SuspectTable suspects={current.suspects} clues={current.clues} />
              </section>
            ) : (
              <ParentNote riddle={episode.content.riddle} />
            )
          }
        />
      </div>
      <div className="mt-10 pl-14">
        <EveningDemo episode={episode} />
      </div>
    </NotebookPage>
  );
}
