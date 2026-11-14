import { useTranslations } from "next-intl";
import { useCallback } from "react";
import { isApiErrorCode, isFieldErrorCode, type ApiErrorCode } from "./errorCodes";
import { toApiError } from "./errors";

// Codes that say nothing to the user: show the request id, so a bug report can be found
// in the logs.
const GENERIC_CODES: readonly ApiErrorCode[] = ["common.http_error", "common.internal_error"];

/** `(error) => text` for any error an RTK Query hook or `unwrap()` gives. */
export function useApiErrorMessage(): (error: unknown) => string {
  const t = useTranslations("common");
  return useCallback(
    (error: unknown) => {
      const { code, requestId } = toApiError(error);
      if (requestId && GENERIC_CODES.includes(code)) return t("unexpectedError", { requestId });
      return t(`errors.${code}`);
    },
    [t],
  );
}

/** `(code) => text` for a code of `ApiError.fields`. */
export function useFieldErrorMessage(): (code: string) => string {
  const t = useTranslations("common");
  return useCallback(
    (code: string) => {
      if (isApiErrorCode(code)) return t(`errors.${code}`);
      if (isFieldErrorCode(code)) return t(`fieldErrors.${code}`);
      return t("fieldErrors.invalid");
    },
    [t],
  );
}

/** `(error) => text` for a form: the code of the first wrong field, else the error itself. */
export function useFormErrorMessage(): (error: unknown) => string {
  const general = useApiErrorMessage();
  const field = useFieldErrorMessage();
  return useCallback(
    (error: unknown) => {
      const [code] = Object.values(toApiError(error).fields ?? {});
      return code ? field(code) : general(error);
    },
    [general, field],
  );
}
