"use client";

import { useFormatter } from "next-intl";
import { caseProgress, useCurrentCase } from "@/features/cases";
import { useFamily, useStartHref } from "@/features/families";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { LandingDesktop } from "./LandingDesktop";
import { LandingMobile } from "./LandingMobile";
import type { Welcome } from "./parts";

/** The wrapper picks the layout and gives both the same data. */
export function Landing() {
  const format = useFormatter();
  const startHref = useStartHref();
  // A visitor without the hint makes no API call; a hint nobody confirms shows the normal landing.
  const hinted = startHref !== "/setup";
  const { family } = useFamily({ skip: !hinted });
  const { current, loading, writing } = useCurrentCase({ skip: !family });

  const welcome: Welcome | undefined =
    family && !loading
      ? {
          names: format.list(family.kids.map((kid) => kid.nickname)),
          count: family.kids.length,
          progress: current ? caseProgress(current, new Date()) : writing ? caseProgress(undefined, new Date()) : undefined,
        }
      : undefined;

  return useIsMobile() ? (
    <LandingMobile startHref={startHref} welcome={welcome} />
  ) : (
    <LandingDesktop startHref={startHref} welcome={welcome} />
  );
}
