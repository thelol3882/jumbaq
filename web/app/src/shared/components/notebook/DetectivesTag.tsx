/** The detectives' names in a header, small, so a family sees that the notebook knows it. */
export function DetectivesTag({ text, className = "" }: { text: string; className?: string }) {
  return <span className={`font-type text-label-sm text-ink-muted ${className}`}>{text}</span>;
}
