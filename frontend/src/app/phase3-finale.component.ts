import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase3Service } from './phase3.service';
import { FinaleState } from './phase3.types';

@Component({
  selector: 'app-phase3-finale',
  standalone: true,
  imports: [CommonModule, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Iron Heights finale">
        <div class="hero-bg hero-bg--finale" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--phase2"></div>
        <section class="phase-layout phase3-layout">
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>
          <section class="phase2-panel phase3-finale-panel">
            <span class="code-panel__eyebrow">Iron Heights</span>
            <h1 class="code-panel__title">Finale</h1>
            <p class="code-panel__subtitle">{{ state.message }}</p>
            <div class="status-banner status-banner--success">{{ state.finalFlag }}</div>
          </section>
        </section>
      </main>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class Phase3FinaleComponent implements OnInit {
  // Finale rendering requires the backend roofAccessGranted gate; direct navigation should stay denied.
  private readonly phase3Service = inject(Phase3Service);
  protected readonly router = inject(Router);
  protected state: FinaleState | null = null;

  ngOnInit(): void {
    this.phase3Service.getFinale().subscribe({
      next: (state) => { this.state = state; },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }
}
