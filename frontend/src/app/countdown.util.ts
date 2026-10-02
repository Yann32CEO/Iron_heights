import { Subscription, interval } from 'rxjs';

export function formatRemainingMs(ms: number): string {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * Counts down from the server-computed remaining time. Only elapsed local time is used,
 * so a player clock that is ahead of or behind the server cannot skew the escape window.
 */
export function startEscapeCountdown(
  remainingMs: number | null | undefined,
  onTick: (label: string) => void,
  onExpire: () => void,
): Subscription {
  if (remainingMs == null) return Subscription.EMPTY;

  const deadline = Date.now() + remainingMs;
  const tick = (): number => {
    const left = Math.max(0, deadline - Date.now());
    onTick(formatRemainingMs(left));
    return left;
  };

  if (tick() <= 0) {
    onExpire();
    return Subscription.EMPTY;
  }

  const subscription = interval(1000).subscribe(() => {
    if (tick() <= 0) {
      subscription.unsubscribe();
      onExpire();
    }
  });
  return subscription;
}
