export function isForbiddenError(error: { status?: number }): boolean {
  return error.status === 401 || error.status === 403;
}
