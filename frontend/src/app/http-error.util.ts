export function isForbiddenError(error: { status?: number }): boolean {
  return error.status === 401 || error.status === 403;
}

/** The backend answers 409 "caught" when an action arrives after the escape window expired. */
export function isCaughtError(error: { status?: number; error?: { detail?: unknown } }): boolean {
  return error.status === 409 && error.error?.detail === 'caught';
}
