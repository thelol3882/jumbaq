export type WritingStepState = "done" | "now" | "todo";

/**
 * A typed checklist of what is being written: a red tick when done, a red box with a typing
 * caret for the step in progress, an empty grey box for later. Each state is also said in words.
 */
export function WritingSteps({
  steps,
  stateLabels,
}: {
  steps: readonly { key: string; label: string; state: WritingStepState }[];
  stateLabels: Record<WritingStepState, string>;
}) {
  return (
    <ol className="flex flex-col gap-3.5">
      {steps.map((s) => (
        <li key={s.key} className="flex items-center gap-3.5">
          <span
            aria-hidden="true"
            className={`flex size-8.5 shrink-0 items-center justify-center border-2 ${
              s.state === "now" ? "border-accent-red" : s.state === "done" ? "border-ink" : "border-ink-faint"
            }`}
          >
            {s.state === "done" ? (
              <svg width="22" height="20" viewBox="0 0 30 26">
                <path
                  d="M3 14 L11 22 L27 3"
                  stroke="var(--color-accent-red)"
                  strokeWidth="3.4"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            ) : null}
          </span>
          <span
            className={`font-type text-case ${
              s.state === "now" ? "font-bold text-ink" : s.state === "done" ? "text-ink-muted" : "text-ink-faint"
            }`}
          >
            {s.label}
            {s.state === "now" ? (
              <span aria-hidden="true" className="ml-1 inline-block h-[1.1em] w-[0.55em] translate-y-[0.18em] bg-accent-red motion-safe:animate-caret" />
            ) : null}
            <span className="sr-only">, {stateLabels[s.state]}</span>
          </span>
        </li>
      ))}
    </ol>
  );
}
