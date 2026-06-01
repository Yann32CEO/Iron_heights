import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { environment } from '../environments/environment';
import { ChangingRoomState, ClosetState, LostBadgeResponse, UniformClaimsResponse } from './changing-room.types';

@Injectable({ providedIn: 'root' })
export class ChangingRoomService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getChangingRoom() {
    return this.http.get<ChangingRoomState>(`${this.baseUrl}/phase1/changing-room`, { withCredentials: true });
  }

  enterChangingRoom() {
    return this.http.post<ChangingRoomState>(`${this.baseUrl}/phase1/changing-room/enter`, {}, { withCredentials: true });
  }

  requestUniform() {
    return this.http.post<ChangingRoomState>(`${this.baseUrl}/phase1/changing-room/uniform`, {}, { withCredentials: true });
  }

  submitLostBadge(guardName: string, guardId: string) {
    return this.http.post<LostBadgeResponse>(`${this.baseUrl}/phase1/changing-room/lost-badge`, { guardName, guardId }, { withCredentials: true });
  }

  queryUniformClaims(filter: string, filterValue: string) {
    return this.http.post<UniformClaimsResponse>(`${this.baseUrl}/phase1/changing-room/uniform-claims`, { filter, filter_value: filterValue }, { withCredentials: true });
  }

  getCloset() {
    return this.http.get<ClosetState>(`${this.baseUrl}/phase1/closet`, { withCredentials: true });
  }

  pickUniform() {
    return this.http.post<ClosetState>(`${this.baseUrl}/phase1/changing-room/pick-uniform`, {}, { withCredentials: true });
  }
}
