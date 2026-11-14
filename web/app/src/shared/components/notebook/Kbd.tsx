/** A key hint for the parent at a keyboard, like ⌘ ↵. Hidden from screen readers: the
 * button it belongs to carries the same action. */
export function KeyHint({ keys, label }: { keys: string[]; label: string }) {
  return (
    <p aria-hidden="true" className="flex items-center gap-2 font-type text-label-sm text-ink-muted">
      {keys.map((key) => (
        <kbd
          key={key}
          className="min-w-5 rounded-sm border-[1.5px] border-ink-muted bg-paper-card px-1.5 text-center font-type text-label-sm text-ink"
        >
          {key}
        </kbd>
      ))}
      <span>{label}</span>
    </p>
  );
}
