import { NotebookPage } from "@/shared/components/notebook";
import { ExampleCase, Headline, ForReviewers, Masthead, Start, Steps } from "./parts";

/** Design D1: one page of the pocket notebook, the stamp at the thumb. */
export function LandingMobile({ startHref }: { startHref: string }) {
  return (
    <NotebookPage>
      <Masthead />
      <div className="mt-5.5">
        <Headline />
      </div>
      <div className="mt-5">
        <Steps />
      </div>
      <div className="mt-6.5 ml-auto">
        <ExampleCase />
      </div>
      <div className="min-h-5 grow" />
      <Start href={startHref} />
      <ForReviewers />
    </NotebookPage>
  );
}
