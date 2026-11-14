import { describe, expect, it } from "vitest";
import { toApiError } from "./errors";

describe("toApiError", () => {
  it("reads the API error body", () => {
    const error = {
      status: 409,
      data: { error: { code: "family.no_session", request_id: "r1", message: "no cookie" } },
    };
    expect(toApiError(error)).toEqual({
      status: 409,
      code: "family.no_session",
      message: "no cookie",
      requestId: "r1",
    });
  });

  it("keeps the field codes, ours and pydantic ones", () => {
    const fields = { kids: "family.kid_nickname_repeated", "kids.0.age": "less_than_equal" };
    const error = { status: 422, data: { error: { code: "common.validation_failed", fields } } };
    expect(toApiError(error)).toMatchObject({ code: "common.validation_failed", fields });
  });

  it("gives a code this build does not know the generic one", () => {
    const error = { status: 400, data: { error: { code: "case.something_new", request_id: "r2" } } };
    expect(toApiError(error)).toMatchObject({ code: "common.http_error", requestId: "r2" });
  });

  it("treats no answer as a network error", () => {
    expect(toApiError({ status: "FETCH_ERROR", error: "TypeError" })).toEqual({
      status: null,
      code: "common.network_error",
    });
    expect(toApiError({ status: "TIMEOUT_ERROR", error: "timeout" }).code).toBe(
      "common.network_error",
    );
  });

  it("treats an answer that is not JSON as an HTTP error", () => {
    const error = { status: "PARSING_ERROR", originalStatus: 502, data: "<html>", error: "" };
    expect(toApiError(error)).toEqual({ status: 502, code: "common.http_error" });
  });

  it("treats anything else as an internal error", () => {
    expect(toApiError({ name: "Error", message: "boom" })).toEqual({
      status: null,
      code: "common.internal_error",
      message: "boom",
    });
    expect(toApiError(undefined)).toEqual({ status: null, code: "common.internal_error" });
  });
});
