import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { environment } from '../environments/environment';
import { CorridorState, KitchenAccessResponse, TimeoutResolution } from './corridor.types';

@Injectable({ providedIn: 'root' })
export class CorridorService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getCorridor() {
    return this.http.get<CorridorState>(`${this.baseUrl}/phase1/corridor`, { withCredentials: true });
  }

  resolveTimeout() {
    return this.http.post<TimeoutResolution>(`${this.baseUrl}/phase1/corridor/timeout`, {}, { withCredentials: true });
  }

  enterYard() {
    return this.http.post<CorridorState>(`${this.baseUrl}/phase1/yard/enter`, {}, { withCredentials: true });
  }

  getYard() {
    return this.http.get<CorridorState>(`${this.baseUrl}/phase1/yard`, { withCredentials: true });
  }

  leaveYard() {
    return this.http.post<CorridorState>(`${this.baseUrl}/phase1/yard/leave`, {}, { withCredentials: true });
  }

  tryKitchen() {
    return this.http.post<KitchenAccessResponse>(`${this.baseUrl}/phase1/kitchen/access`, {}, { withCredentials: true });
  }

  enterChangingRoom() {
    return this.http.post<CorridorState>(`${this.baseUrl}/phase1/changing-room/enter`, {}, { withCredentials: true });
  }

  returnToCell() {
    return this.http.post<CorridorState>(`${this.baseUrl}/phase1/return-to-cell`, {}, { withCredentials: true });
  }
}
