/**
 * Read a failed API call without showing users how the system works.
 *
 * The backend answers with an HTTP status, and often a machine-readable
 * `code` and a developer-facing message (`error` / `detail`) that can name
 * internal permissions or record ids. Screens use `code` and `status` to
 * pick their own plain-language message; the raw strings are never shown.
 */
export interface ApiErrorInfo {
  status?: number;
  code?: string;
  /** DRF field errors, e.g. { email: ["Enter a valid email address."] } */
  fieldErrors: Record<string, string>;
}

export const readApiError = (error: unknown): ApiErrorInfo => {
  const response = (error as { response?: { status?: number; data?: unknown } })?.response;
  const data =
    response?.data && typeof response.data === "object"
      ? (response.data as Record<string, unknown>)
      : {};
  const fieldErrors: Record<string, string> = {};
  for (const [field, value] of Object.entries(data)) {
    if (Array.isArray(value) && typeof value[0] === "string") fieldErrors[field] = value[0];
  }
  return {
    status: response?.status,
    code: typeof data.code === "string" ? data.code : undefined,
    fieldErrors,
  };
};

export const NO_PERMISSION = "You don't have permission to do this.";
