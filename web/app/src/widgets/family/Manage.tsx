"use client";

import { ManageSubscription, useGetSubscriptionQuery } from "@/features/billing";

/** The way to manage or cancel, only for a family with a subscription. */
export function Manage() {
  const { data } = useGetSubscriptionQuery();
  return data?.active ? <ManageSubscription /> : null;
}
