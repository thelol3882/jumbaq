import type { ReactNode } from "react";

/** A small block for reviewers, below the main action: never part of the read-aloud text. */
export function DemoControls({ title, note, children }: { title: string; note: string; children: ReactNode }) {
  return (
    <section className="flex max-w-xl flex-col items-start gap-1 border-t border-dashed border-rule-strong pt-4">
      <h2 className="font-type text-label font-normal text-ink-muted">{title}</h2>
      <p className="font-type text-label font-normal text-ink-muted">{note}</p>
      <div className="flex flex-col items-start gap-1">{children}</div>
    </section>
  );
}
