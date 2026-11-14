import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

// The primary action: red pencil text in a double red border, like a rubber stamp.
const STAMP =
  "flex min-h-16 w-full items-center justify-center rounded-sm border-3 border-primary-border " +
  "bg-primary-bg px-4 font-type text-button text-primary-fg outline-1 -outline-offset-8 " +
  "outline-primary-border transition-colors active:bg-primary-pressed-bg " +
  "active:text-primary-pressed-fg disabled:cursor-progress disabled:opacity-70";

type Tilt = "none" | "left" | "right";
const TILT: Record<Tilt, string> = { none: "", left: "-rotate-[0.8deg]", right: "rotate-[0.6deg]" };

export function StampButton({
  tilt = "left",
  className = "",
  ...props
}: ComponentProps<"button"> & { tilt?: Tilt }) {
  return <button type="button" className={`${STAMP} ${TILT[tilt]} ${className}`} {...props} />;
}

export function StampLink({
  href,
  tilt = "left",
  children,
}: {
  href: string;
  tilt?: Tilt;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={`${STAMP} ${TILT[tilt]}`}>
      {children}
    </Link>
  );
}
