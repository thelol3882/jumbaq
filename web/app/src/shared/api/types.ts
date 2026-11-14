import type { components, paths } from "./schema";

/** Request and response bodies of the API, by their backend (Pydantic) name. */
export type Schemas = components["schemas"];

/** Query string parameters of an endpoint, e.g. `QueryParams<"/api/v1/jobs", "get">`. */
export type QueryParams<P extends keyof paths, M extends keyof paths[P]> = paths[P][M] extends {
  parameters: { query?: infer Q };
}
  ? NonNullable<Q>
  : never;
