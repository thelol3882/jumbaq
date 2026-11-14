import { NotebookPage } from "@/shared/components/notebook";
import { ExampleCase, Headline, Masthead, Start, Steps } from "./parts";

/** The notebook opened flat: the story on the left page, the case and the stamp on the right. */
export function LandingDesktop({ startHref }: { startHref: string }) {
  return (
    <NotebookPage width="wide">
      <div className="flex flex-col">
        <Masthead />
      </div>
      <div className="my-auto grid grid-cols-2 gap-16 py-12">
        <div className="flex flex-col gap-8">
          <Headline large />
          <Steps />
        </div>
        <div className="flex flex-col items-center justify-center gap-10 border-l border-dashed border-rule-divider pl-16">
          <ExampleCase />
          <div className="w-full max-w-sm">
            <Start href={startHref} />
          </div>
        </div>
      </div>
    </NotebookPage>
  );
}
