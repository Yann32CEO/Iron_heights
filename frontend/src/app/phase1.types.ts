export interface Phase1CellState {
  alias: string;
  role: string;
  scene: string;
  caughtCount: number;
  instructions: {
    title: string;
    body: string[];
  };
  lockCiphertext: string;
  escaped: boolean;
}

export interface Phase1CellOpenResponse {
  success: boolean;
  scene: string;
  flag?: string | null;
  error?: string | null;
}
