export const CORRIDOR_DURATION_MS = 90 * 1000;

export function getRemainingMs(escapedAt: string | null | undefined): number {
  if (!escapedAt) return CORRIDOR_DURATION_MS;
  const escapedAtMs = new Date(escapedAt).getTime();
  const deadline = escapedAtMs + CORRIDOR_DURATION_MS;
  return Math.max(0, deadline - Date.now());
}

export function formatRemainingMs(ms: number): string {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}
