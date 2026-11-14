/** The wordmark as type: Courier Prime, always lower case, with the red pencil loop. */
export function Wordmark({ text, size = "lg" }: { text: string; size?: "lg" | "sm" }) {
  if (size === "sm") return <span className="font-type text-xl font-bold">{text}</span>;
  return (
    <span className="relative inline-block py-1.5 pr-4.5 pl-2.5">
      <span className="font-type text-wordmark">{text}</span>
      <svg
        aria-hidden="true"
        width="210"
        height="72"
        viewBox="0 0 210 72"
        className="pointer-events-none absolute -top-1.5 -left-2"
      >
        <path
          d="M14 40 C 8 14, 120 2, 190 16 C 214 22, 206 56, 150 62 C 90 70, 18 64, 10 44 C 6 32, 30 18, 60 12"
          stroke="var(--color-accent-red)"
          strokeWidth="2.4"
          fill="none"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
