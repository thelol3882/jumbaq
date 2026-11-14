import { baseApi } from "@/shared/api/baseApi";
import type { Schemas } from "@/shared/api/types";

export const billingApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // The answer is the Stripe payment page; Stripe sends the parent back to /billing/*.
    startCheckout: builder.mutation<Schemas["CheckoutOut"], void>({
      query: () => ({ url: "/billing/checkout", method: "POST" }),
    }),
    getSubscription: builder.query<Schemas["SubscriptionOut"], void>({
      query: () => "/billing/subscription",
      providesTags: ["Subscription"],
    }),
  }),
});

export const { useStartCheckoutMutation, useGetSubscriptionQuery } = billingApi;
