import { NotebookPage } from "@/shared/components/notebook";
import { ExampleCase, Headline, ForReviewers, Masthead, Start, Steps, WelcomeCard, type Welcome } from "./parts";

/** Design D1: one page of the pocket notebook, the stamp at the thumb. */
export function LandingMobile({ startHref, welcome }: { startHref: string; welcome: Welcome | undefined }) {
  return (
    <NotebookPage>
      <Masthead tag={welcome?.tag} />
      <div className="mt-5.5">
        <Headline />
      </div>
      <div className="mt-5">
        <Steps />
      </div>
      {welcome ? null : (
        <div className="mt-6.5 ml-auto">
          <ExampleCase />
        </div>
      )}
      <div className="min-h-5 grow" />
      {welcome ? <WelcomeCard welcome={welcome} /> : <Start href={startHref} />}
      <ForReviewers />
    </NotebookPage>
  );
}
