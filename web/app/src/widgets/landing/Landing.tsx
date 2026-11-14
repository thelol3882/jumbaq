"use client";

import { useStartHref } from "@/features/families";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { LandingDesktop } from "./LandingDesktop";
import { LandingMobile } from "./LandingMobile";

/** The wrapper picks the layout and gives both the same data. */
export function Landing() {
  const startHref = useStartHref();
  return useIsMobile() ? <LandingMobile startHref={startHref} /> : <LandingDesktop startHref={startHref} />;
}
