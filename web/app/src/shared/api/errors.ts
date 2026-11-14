import { isApiErrorCode, type ApiErrorCode } from "./errorCodes";

export type ApiError = {
  /** HTTP status, or null when there was no answer. */
  status: number | null;
  code: ApiErrorCode;
  /** For developers only; show text by `code`. */
  message?: string;
  requestId?: string;
  /** Field name (nested with dots, like `addresses.0.lng`) to a field code. */
  fields?: Record<string, string>;
};

type Body = Record<string, unknown>;

/**
 * Turns what RTK Query rejects with (`FetchBaseQueryError` or `SerializedError`) into
 * one shape. The API answers `{ error: { code, request_id, message?, fields? } }`.
 */
export function toApiError(error: unknown): ApiError {
  if (!isRecord(error)) return { status: null, code: "common.internal_error" };
  const { status } = error;
  if (status === "FETCH_ERROR" || status === "TIMEOUT_ERROR") {
    return { status: null, code: "common.network_error" };
  }
  // An answer that is not JSON, like a 502 page of the proxy.
  if (status === "PARSING_ERROR") {
    const originalStatus = typeof error.originalStatus === "number" ? error.originalStatus : null;
    return { status: originalStatus, code: "common.http_error" };
  }
  if (typeof status === "number") return fromBody(status, error.data);
  return { status: null, code: "common.internal_error", message: optionalString(error.message) };
}

function fromBody(status: number, data: unknown): ApiError {
  const body = isRecord(data) && isRecord(data.error) ? data.error : {};
  return {
    status,
    // A code this build does not know yet (a newer API) gets the generic message.
    code: isApiErrorCode(body.code) ? body.code : "common.http_error",
    message: optionalString(body.message),
    requestId: optionalString(body.request_id),
    fields: isStringRecord(body.fields) ? body.fields : undefined,
  };
}

function isRecord(value: unknown): value is Body {
  return typeof value === "object" && value !== null;
}

function isStringRecord(value: unknown): value is Record<string, string> {
  return isRecord(value) && Object.values(value).every((item) => typeof item === "string");
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}
