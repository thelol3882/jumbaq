import type { ReactNode } from "react";

/**
 * A page of the field notebook: dot grid paper, and on reading screens the red margin
 * rule. `width` is the column of text, not the page: the paper fills the screen.
 */
export function NotebookPage({
  children,
  margin = false,
  width = "narrow",
}: {
  children: ReactNode;
  margin?: boolean;
  width?: "narrow" | "wide";
}) {
  const column = width === "narrow" ? "max-w-[26rem]" : "max-w-5xl";
  return (
    <div className="relative min-h-dvh overflow-x-hidden bg-dot-grid font-story text-ink">
      <main
        className={`relative mx-auto flex min-h-dvh w-full ${column} flex-col px-5.5 pt-5 pb-7 ${margin ? "pl-14" : ""}`}
      >
        {margin ? (
          <span aria-hidden="true" className="absolute inset-y-0 left-10.5 border-l-[1.5px] border-rule-margin" />
        ) : null}
        {children}
      </main>
    </div>
  );
}
