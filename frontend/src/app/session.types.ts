export interface SessionState {
  alias: string;
  role: string;
  phase: string;
  scene: string;
}

export interface SessionProfile extends SessionState {
  flags: string[];
}
