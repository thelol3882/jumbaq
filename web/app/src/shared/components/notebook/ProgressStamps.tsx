/**
 * A row of rubber stamps: red pencil and tilted once that step is done, a faint dashed outline
 * until then. Nothing moves, so a stamp never pretends to progress; each also says its state.
 */
export function ProgressStamps({
  stamps,
  doneLabel,
  notYetLabel,
}: {
  stamps: readonly { key: string; label: string; done: boolean }[];
  doneLabel: string;
  notYetLabel: string;
}) {
  return (
    <ol className="flex flex-wrap gap-2.5">
      {stamps.map((s, index) => (
        <li
          key={s.key}
          className={`flex min-h-11 items-center gap-2 rounded-sm px-3 font-type text-label ${
            s.done
              ? `border-3 border-success-border font-bold text-success-fg outline-1 -outline-offset-6 outline-success-border ${
                  index % 2 ? "rotate-[1.5deg]" : "-rotate-[2deg]"
                }`
              : "border-[1.5px] border-dashed border-rule-divider text-ink-faint"
          }`}
        >
          <span aria-hidden="true">{index + 1}</span>
          {s.label}
          <span className="sr-only">, {s.done ? doneLabel : notYetLabel}</span>
        </li>
      ))}
    </ol>
  );
}
