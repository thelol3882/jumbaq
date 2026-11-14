import { baseApi } from "@/shared/api/baseApi";
import type { Checkout, Portal, Subscription } from "../types";

export const billingApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // The answer is the Stripe payment page; Stripe sends the parent back to /billing/*.
    startCheckout: builder.mutation<Checkout, void>({
      query: () => ({ url: "/billing/checkout", method: "POST" }),
    }),
    // The answer is the Stripe portal page, where the family manages or cancels; it returns to /family.
    openPortal: builder.mutation<Portal, void>({
      query: () => ({ url: "/billing/portal", method: "POST" }),
    }),
    getSubscription: builder.query<Subscription, void>({
      query: () => "/billing/subscription",
      providesTags: ["Subscription"],
    }),
  }),
});

export const { useStartCheckoutMutation, useOpenPortalMutation, useGetSubscriptionQuery } = billingApi;
