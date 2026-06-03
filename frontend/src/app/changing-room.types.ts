export interface ChangingRoomState {
  alias: string;
  role: string;
  scene: string;
  escapedAt: string | null;
  timerDisabled: boolean;
  caughtCount: number;
  uniformDenied: boolean;
  lostBadgeMessage: string;
  lostBadgeVariant: string;
  temporaryBadgeIssued: boolean;
  staffRelayIssued: boolean;
}

export interface LostBadgeResponse {
  success: boolean;
  busted: boolean;
  message: string;
  stage: string;
  temporaryBadgeIssued: boolean;
  remainingNameAttempts: number;
}

export interface UniformClaimsResponse {
  success: boolean;
  message: string;
  matched: boolean;
  error: boolean;
}

export interface ClosetState {
  alias: string;
  role: string;
  scene: string;
  escapedAt: string | null;
  timerDisabled: boolean;
  caughtCount: number;
  uniformCollected: boolean;
  flag?: string | null;
}
