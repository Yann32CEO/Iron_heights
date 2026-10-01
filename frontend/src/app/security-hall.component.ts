import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase2Service } from './phase2.service';
import { Phase2State } from './phase2.types';

@Component({
  selector: 'app-security-hall',
  standalone: true,
  imports: [CommonModule, RouterLink, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Phase 2 security hall">
        <div class="hero-bg hero-bg--security-hall" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--phase2"></div>

        <section class="phase-layout phase2-layout">
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>

          <section class="hud-stack" aria-label="Phase 2 status panels">
            <button class="status-hud-card status-hud-card--compact status-hud-card--button" type="button" (click)="showStatusPopup = true">
              <span class="status-hud-card__label">Operational Status</span>
              <strong>{{ state.exposure.state }}</strong>
              <small class="phase2-status-copy">{{ state.exposure.message }}</small>
            </button>
            <div class="status-hud-card status-hud-card--compact">
              <span class="status-hud-card__label">Times Caught</span>
              <strong>{{ state.caughtCount }}</strong>
            </div>
          </section>

          <section class="phase2-panel" aria-label="Security hall overview">
            <span class="code-panel__eyebrow">Security Administration Block</span>
            <h1 class="code-panel__title">Phase 2 Entry</h1>
            <p class="code-panel__subtitle">Operational support, internal review, and executive routing are monitored in this block. ARTEMIS can assist, but unusual behavior will not stay invisible for long.</p>
            <div class="status-banner">All staff interactions in this sector are logged and heavily monitored. Kitchen service feedback may be referenced during route and delivery summaries.</div>
          </section>

          <div class="utility-zone utility-zone--right">
            <button class="action-button action-button--ghost" type="button" (click)="showInfo = true">Info</button>
          </div>

          <nav class="phase2-nav phase2-nav--horizontal" aria-label="Phase 2 navigation">
            <a class="action-button phase2-nav__button" routerLink="/phase2/security-hall">Security Hall</a>
            <a class="action-button phase2-nav__button" routerLink="/phase2/artemis">ARTEMIS</a>
            <a class="action-button phase2-nav__button" routerLink="/phase2/kitchen-sector">Kitchen Sector</a>
            <a class="action-button phase2-nav__button" routerLink="/phase2/director-office">Director's Office</a>
          </nav>
        </section>

        @if (showInfo) {
          <div class="info-modal" role="dialog" aria-modal="true">
            <div class="info-modal__backdrop" (click)="showInfo = false"></div>
            <section class="info-modal__card">
              <div class="info-modal__header">
                <h2>{{ state.instructions?.title || 'Phase 2 Instructions' }}</h2>
                <button class="close-button" type="button" (click)="showInfo = false">×</button>
              </div>
              <div class="info-modal__body">
                @for (line of state.instructions?.body || []; track line) { <p>{{ line }}</p> }
              </div>
            </section>
          </div>
        }

        @if (showStatusPopup) {
          <div class="info-modal" role="dialog" aria-modal="true">
            <div class="info-modal__backdrop" (click)="showStatusPopup = false"></div>
            <section class="info-modal__card status-popup-modal">
              <div class="info-modal__header">
                <h2>Operational Status Update</h2>
                <button class="close-button" type="button" (click)="showStatusPopup = false">×</button>
              </div>
              <div class="info-modal__body">
                <p><strong>Current State:</strong> {{ state.exposure.state }}</p>
                <p>{{ state.exposure.message }}</p>
              </div>
            </section>
          </div>
        }
      </main>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class SecurityHallComponent implements OnInit {
  private readonly phase2Service = inject(Phase2Service);
  private readonly router = inject(Router);

  protected state: Phase2State | null = null;
  protected showInfo = false;
  protected showStatusPopup = false;

  ngOnInit(): void {
    this.phase2Service.getSecurityHall().subscribe({
      next: (state) => { this.state = state; },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }
}
