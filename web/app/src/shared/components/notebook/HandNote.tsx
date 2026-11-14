import type { ReactNode } from "react";

/** A short note in ballpoint blue for the parent only. Never story text or a button. */
export function HandNote({
  lead,
  children,
  className = "",
}: {
  lead?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <p className={`font-hand text-note text-note-fg ${className}`}>
      {lead ? <b className="font-bold">{lead} </b> : null}
      {children}
    </p>
  );
}
