import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { environment } from '../environments/environment';
import { SessionProfile, SessionState } from './session.types';

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getCurrentSession() {
    return this.http.get<SessionState>(`${this.baseUrl}/session/me`, {
      withCredentials: true,
    });
  }

  getProfile() {
    return this.http.get<SessionProfile>(`${this.baseUrl}/session/profile`, {
      withCredentials: true,
    });
  }

  createSession(alias: string) {
    return this.http.post<SessionState>(
      `${this.baseUrl}/session/intake`,
      { alias },
      { withCredentials: true },
    );
  }
}
