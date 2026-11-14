// Mirror of backend/jumbaq/core/error_codes.py: the values are translation keys
// (common.errors.<code> in src/i18n/messages/en.json) and never change once used.
// backend/tests/test_error_codes.py fails when the two differ.
export const API_ERROR_CODES = [
  "common.bad_request",
  "common.not_found",
  "common.method_not_allowed",
  "common.conflict",
  "common.too_large",
  "common.too_many_requests",
  "common.validation_failed",
  "common.http_error",
  "common.internal_error",
  "common.not_authenticated",
  "common.forbidden",
  "family.no_session",
  "family.kid_nickname_repeated",
  "ai.daily_limit_reached",
  "ai.disabled",
  "ai.bad_output",
  "ai.unavailable",
  "billing.payment_required",
  "billing.already_subscribed",
  "billing.bad_signature",
  "billing.not_configured",
  "billing.unavailable",
  "billing.no_subscription",
  "case.not_found",
  "case.not_accusing",
  "case.not_solved",
  "case.unknown_suspect",
  "episode.not_found",
  "episode.not_ready",
  "episode.not_available_yet",
  "episode.already_swapped",
  "episode.demo_mode_off",
  "episode.wrong_step",
  // Ours, not the API's: the request got no answer.
  "common.network_error",
] as const;

export type ApiErrorCode = (typeof API_ERROR_CODES)[number];

// Field codes that are not in API_ERROR_CODES: the pydantic error types our request bodies
// can produce (common.fieldErrors.<code> in en.json).
export const FIELD_ERROR_CODES = [
  "missing",
  "string_too_short",
  "string_too_long",
  "too_short",
  "too_long",
  "int_parsing",
  "greater_than_equal",
  "less_than_equal",
] as const;

export type FieldErrorCode = (typeof FIELD_ERROR_CODES)[number];

export function isApiErrorCode(code: unknown): code is ApiErrorCode {
  return (API_ERROR_CODES as readonly unknown[]).includes(code);
}

export function isFieldErrorCode(code: unknown): code is FieldErrorCode {
  return (FIELD_ERROR_CODES as readonly unknown[]).includes(code);
}
