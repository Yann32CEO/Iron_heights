// Keep these interfaces aligned with backend/app/schemas/phase3.py; Phase 3 uses camelCase over the wire.
export interface Phase3InterceptPayload {
  alg: string;
  iv: string;
  ciphertext: string;
}

export interface DiaryEntryPayload {
  id: number;
  subject: string;
  content: string;
  archived: boolean;
}

export interface DirectorOfficeInsideState {
  alias: string;
  role: string;
  phase: string;
  scene: string;
  caughtCount: number;
  directorLetter: string;
  intercept: Phase3InterceptPayload;
  directorJwtAccepted: boolean;
  directorDiaryUnlocked: boolean;
  roofCodeAccepted: boolean;
  roofAccessGranted: boolean;
}

export interface DirectorRelayResponse {
  success: boolean;
  message: string;
  directorJwtAccepted: boolean;
  directorDiaryUnlocked: boolean;
  role: string;
  alertFlag: string;
}

export interface DirectorDiaryState {
  alias: string;
  role: string;
  totalEntries: number;
  activeSubject: string;
  activeContent: string;
  createdEntries: DiaryEntryPayload[];
}

export interface DiaryEntryResponse {
  success: boolean;
  message: string;
  entry?: DiaryEntryPayload | null;
}

export interface DuplicateDiaryEntryResponse {
  error: 'duplicate_subject';
  message: string;
  existingEntry: DiaryEntryPayload;
}

export interface RoofAccessResponse {
  success: boolean;
  roofCodeAccepted: boolean;
  roofAccessGranted: boolean;
  message: string;
  alertFlag: string;
  redirectTo?: string | null;
}

export interface FinaleState {
  alias: string;
  role: string;
  finalFlag: string;
  message: string;
}
