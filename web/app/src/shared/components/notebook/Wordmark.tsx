/** The wordmark as type: Courier Prime, always lower case, with the red pencil loop. */
export function Wordmark({ text, size = "lg" }: { text: string; size?: "sm" | "lg" | "xl" }) {
  if (size === "sm") return <span className="font-type text-xl font-bold">{text}</span>;
  const xl = size === "xl";
  return (
    <span className={`relative inline-block ${xl ? "py-2 pr-6 pl-3" : "py-1.5 pr-4.5 pl-2.5"}`}>
      <span className={`font-type ${xl ? "text-[4rem] leading-none font-bold tracking-[-0.01em]" : "text-wordmark"}`}>
        {text}
      </span>
      <svg
        aria-hidden="true"
        width={xl ? 290 : 210}
        height={xl ? 98 : 72}
        viewBox="0 0 210 72"
        className={`pointer-events-none absolute ${xl ? "-top-2 -left-2.5" : "-top-1.5 -left-2"}`}
      >
        <path
          d="M14 40 C 8 14, 120 2, 190 16 C 214 22, 206 56, 150 62 C 90 70, 18 64, 10 44 C 6 32, 30 18, 60 12"
          stroke="var(--color-accent-red)"
          strokeWidth={xl ? 2 : 2.4}
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
