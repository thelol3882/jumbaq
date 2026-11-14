import { baseApi } from "@/shared/api/baseApi";
import { listTags } from "@/shared/api/tags";
import type { Accusation, Case, Certificate, SolvedCase } from "../types";

export const casesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // 404 case.not_found for a moment after the setup, until the worker opens case 1.
    getCurrentCase: builder.query<Case, void>({
      query: () => "/cases/current",
      providesTags: ["Case"],
    }),
    // 402 billing.payment_required for a case after the free ones without a subscription.
    startNextCase: builder.mutation<Case, void>({
      query: () => ({ url: "/cases", method: "POST" }),
      invalidatesTags: ["Case", "Episode"],
    }),
    // A wrong suspect is not an error: `correct` is false.
    accuse: builder.mutation<Accusation, { caseId: string; suspectId: string }>({
      query: ({ caseId, suspectId }) => ({
        url: `/cases/${caseId}/accuse`,
        method: "POST",
        body: { suspect_id: suspectId },
      }),
      invalidatesTags: ["Case"],
    }),
    // The solved cases, newest first: past cases and their certificates.
    getSolvedCases: builder.query<SolvedCase[], void>({
      query: () => "/cases",
      providesTags: (result) => listTags("Case", result),
    }),
    getCertificate: builder.query<Certificate, string>({
      query: (caseId) => `/cases/${caseId}/certificate`,
      providesTags: (_result, _error, caseId) => [{ type: "Case", id: caseId }],
    }),
  }),
});

export const {
  useGetCurrentCaseQuery,
  useStartNextCaseMutation,
  useAccuseMutation,
  useGetCertificateQuery,
  useGetSolvedCasesQuery,
} = casesApi;
