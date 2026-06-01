import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';

import { environment } from '../environments/environment';
import {
  ArtemisChatResponse,
  DirectorDoorResponse,
  KitchenOrderResponse,
  KitchenReviewResponse,
  Phase2State,
  ResetCheckpointResponse,
} from './phase2.types';

@Injectable({ providedIn: 'root' })
export class Phase2Service {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getSecurityHall() {
    return this.http.get<Phase2State>(`${this.baseUrl}/phase2/security-hall`, { withCredentials: true });
  }

  getArtemis() {
    return this.http.get<Phase2State>(`${this.baseUrl}/phase2/artemis`, { withCredentials: true });
  }

  chatArtemis(prompt: string) {
    return this.http.post<ArtemisChatResponse>(`${this.baseUrl}/phase2/artemis/chat`, { prompt }, { withCredentials: true });
  }

  getKitchenSector() {
    return this.http.get<Phase2State>(`${this.baseUrl}/phase2/kitchen-sector`, { withCredentials: true });
  }

  orderMeal(mealId: string) {
    return this.http.post<KitchenOrderResponse>(`${this.baseUrl}/phase2/kitchen/order`, { mealId }, { withCredentials: true });
  }

  submitReview(payload: { mealId: string; rating: string; reviewerName: string; text: string }) {
    return this.http.post<KitchenReviewResponse>(`${this.baseUrl}/phase2/kitchen/review`, payload, { withCredentials: true });
  }

  getDirectorOffice() {
    return this.http.get<Phase2State>(`${this.baseUrl}/phase2/director-office`, { withCredentials: true });
  }

  submitDirectorCode(code: string) {
    return this.http.post<DirectorDoorResponse>(`${this.baseUrl}/phase2/director-door`, { code }, { withCredentials: true });
  }

  resetCheckpoint() {
    return this.http.post<ResetCheckpointResponse>(`${this.baseUrl}/phase2/reset-checkpoint`, {}, { withCredentials: true });
  }
}
