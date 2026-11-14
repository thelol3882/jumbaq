/** The riddle on a taped index card with ruled lines. Read-aloud text, so Literata. */
export function RiddleCard({ label, text, size = "md" }: { label: string; text: string; size?: "md" | "lg" }) {
  const type = size === "lg" ? "text-[1.875rem] leading-[45px] bg-[length:100%_45px]" : "text-riddle leading-[36px]";
  return (
    <div className="relative -rotate-[1.2deg]">
      <span aria-hidden="true" className="absolute -top-3 left-[46%] z-10 h-6 w-20 rotate-3 bg-tag-tape" />
      <div className="border border-riddle-border bg-riddle-bg px-6 pt-5 pb-4">
        <p className="font-type text-label-sm text-riddle-label">{label}</p>
        <p className={`mt-2 bg-riddle-lines font-story font-medium italic text-riddle-fg ${type}`}>{text}</p>
      </div>
    </div>
  );
}
