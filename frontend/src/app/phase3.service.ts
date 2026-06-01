import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { environment } from '../environments/environment';
import {
  DiaryEntryResponse,
  DirectorDiaryState,
  DirectorOfficeInsideState,
  DirectorRelayResponse,
  FinaleState,
  RoofAccessResponse,
} from './phase3.types';

@Injectable({ providedIn: 'root' })
export class Phase3Service {
  // All Phase 3 calls depend on cookies: ih_session for continuity, staffRelay for Director escalation.
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getDirectorOfficeInside() {
    return this.http.get<DirectorOfficeInsideState>(`${this.baseUrl}/phase3/director-office/inside`, { withCredentials: true });
  }

  resyncDirectorRelay() {
    return this.http.post<DirectorRelayResponse>(`${this.baseUrl}/phase3/director-relay/resync`, {}, { withCredentials: true });
  }

  getDirectorDiary() {
    return this.http.get<DirectorDiaryState>(`${this.baseUrl}/phase3/director-diary`, { withCredentials: true });
  }

  createDiaryEntry(subject: string, content: string) {
    return this.http.post<DiaryEntryResponse>(`${this.baseUrl}/phase3/diary/entries`, { subject, content }, { withCredentials: true });
  }

  submitRoofCode(code: string) {
    return this.http.post<RoofAccessResponse>(`${this.baseUrl}/phase3/roof-access`, { code }, { withCredentials: true });
  }

  getFinale() {
    return this.http.get<FinaleState>(`${this.baseUrl}/phase3/finale`, { withCredentials: true });
  }
}
