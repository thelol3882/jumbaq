import type { ReactNode } from "react";

/**
 * The notebook opened flat on a wide screen: the main page on the left, the parent's page
 * on the right, with a dashed fold between them. Below 900 px the pages stack.
 */
export function NotebookSpread({
  main,
  side,
  sideLabel,
}: {
  main: ReactNode;
  side: ReactNode;
  sideLabel: string;
}) {
  return (
    <div className="flex flex-wrap">
      <div className="min-w-0 grow-[999] basis-[560px] pr-16">{main}</div>
      <aside
        aria-label={sideLabel}
        className="flex min-w-0 grow basis-[360px] flex-col gap-8 border-l-[1.5px] border-dashed border-rule-divider pl-16"
      >
        {side}
      </aside>
    </div>
  );
}
