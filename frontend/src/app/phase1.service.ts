import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { environment } from '../environments/environment';
import { Phase1CellOpenResponse, Phase1CellState } from './phase1.types';

@Injectable({ providedIn: 'root' })
export class Phase1Service {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getCellState() {
    return this.http.get<Phase1CellState>(`${this.baseUrl}/phase1/cell`, {
      withCredentials: true,
    });
  }

  openCell(cellCode: string) {
    return this.http.post<Phase1CellOpenResponse>(
      `${this.baseUrl}/phase1/cell/open`,
      { cellCode },
      { withCredentials: true },
    );
  }
}
