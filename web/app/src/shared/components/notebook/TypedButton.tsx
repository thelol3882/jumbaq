import type { ComponentProps } from "react";

/** The second action: typewriter text with a dotted underline ("Need a hint"). */
export function TypedButton({ className = "", ...props }: ComponentProps<"button">) {
  return (
    <button
      type="button"
      className={
        "min-h-12 px-1 font-type text-case font-normal text-secondary-fg underline decoration-dotted " +
        `decoration-2 underline-offset-[5px] ${className}`
      }
      {...props}
    />
  );
}
