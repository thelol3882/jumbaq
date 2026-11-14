import type { ReactNode } from "react";

/** A manila evidence tag with a punched hole and a strip of tape. */
export function EvidenceTag({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="relative">
      <span aria-hidden="true" className="absolute -top-2.5 left-20 z-10 h-5.5 w-18 -rotate-[4deg] bg-tag-tape" />
      <div className="relative bg-evidence-bg py-4 pr-4 pl-9 [clip-path:polygon(18px_0,100%_0,100%_100%,18px_100%,0_50%)]">
        <span
          aria-hidden="true"
          className="absolute top-1/2 left-3.5 -mt-1.5 size-2.5 rounded-full border border-evidence-edge bg-paper"
        />
        <p className="font-type text-label-sm text-evidence-label">{label}</p>
        <div className="mt-1 font-story text-body-sm font-semibold text-evidence-fg">{children}</div>
      </div>
    </div>
  );
}
