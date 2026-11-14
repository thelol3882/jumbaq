import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { apiUrl } from "@/shared/config/env";

// The API asks for this header on every change: a form or a plain fetch from another site
// cannot send it without a CORS preflight (backend/jumbaq/core/csrf.py).
export const CSRF_HEADER = "X-Requested-With";
export const CSRF_VALUE = "jumbaq";

export const TAG_TYPES = ["Family", "Case", "Episode", "Subscription"] as const;
export type TagType = (typeof TAG_TYPES)[number];

// The one API slice; features add endpoints with `baseApi.injectEndpoints()`.
// `credentials: "include"` sends the HttpOnly family_session cookie of the API host.
export const baseApi = createApi({
  reducerPath: "api",
  baseQuery: fetchBaseQuery({
    baseUrl: apiUrl,
    credentials: "include",
    prepareHeaders: (headers) => {
      headers.set(CSRF_HEADER, CSRF_VALUE);
      return headers;
    },
  }),
  tagTypes: TAG_TYPES,
  endpoints: () => ({}),
});
