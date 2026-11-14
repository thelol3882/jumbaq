import { baseApi } from "@/shared/api/baseApi";
import type { Family, FamilyCreate } from "../types";

export const familiesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // The answer also sets the family_session cookie on the API host.
    createFamily: builder.mutation<Family, FamilyCreate>({
      query: (body) => ({ url: "/families", method: "POST", body }),
      invalidatesTags: ["Family"],
    }),
    // 401 family.no_session when this browser has no family yet.
    getFamily: builder.query<Family, void>({
      query: () => "/family",
      providesTags: ["Family"],
    }),
  }),
});

export const { useCreateFamilyMutation, useGetFamilyQuery } = familiesApi;
