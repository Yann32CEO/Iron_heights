export interface CorridorState {
  alias: string;
  role: string;
  scene: string;
  escapedAt: string | null;
  remainingMs: number | null;
  timerDisabled: boolean;
  caughtCount: number;
  kitchenDenied: boolean;
}

export interface TimeoutResolution {
  caught: boolean;
  redirectTo: string;
}

export interface KitchenAccessResponse {
  allowed: boolean;
  kitchenDenied: boolean;
  redirectTo?: string | null;
}
