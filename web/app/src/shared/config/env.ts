const apiOrigin = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Prefix of every API endpoint. */
export const apiUrl = `${apiOrigin}/api/v1`;
