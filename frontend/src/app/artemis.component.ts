import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase2Service } from './phase2.service';
import { ExposurePayload, Phase2State } from './phase2.types';

@Component({
  selector: 'app-artemis',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="ARTEMIS terminal room">
        <div class="hero-bg hero-bg--artemis" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--phase2"></div>
        <section class="phase-layout phase2-layout">
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>
          <section class="hud-stack">
            <button class="status-hud-card status-hud-card--compact status-hud-card--button" type="button" (click)="openStatusPopup(exposure)"><span class="status-hud-card__label">Operational Status</span><strong>{{ exposure.state }}</strong><small class="phase2-status-copy">{{ exposure.message }}</small></button>
            <div class="status-hud-card status-hud-card--compact"><span class="status-hud-card__label">Times Caught</span><strong>{{ state.caughtCount }}</strong></div>
          </section>
          <section class="phase2-panel phase2-panel--terminal">
            <span class="code-panel__eyebrow">ARTEMIS // Facility Operations Assistant</span>
            <h1 class="code-panel__title">Operational Support Console</h1>
            <div class="artemis-console__meta"><span>Prompt window</span><strong>{{ promptCount }} / {{ promptLimit }}</strong></div>
            <div class="artemis-console__reply" [class.artemis-console__reply--thinking]="thinking">{{ thinking ? 'thinking...' : reply }}</div>
            <form class="changing-room-form" (ngSubmit)="submitPrompt()">
              <input class="code-panel__input" type="text" [(ngModel)]="prompt" name="prompt" placeholder="Ask ARTEMIS" />
              <button class="action-button" type="submit" [disabled]="submitting || !prompt.trim()">{{ submitting ? 'Querying...' : 'Send to ARTEMIS' }}</button>
            </form>
          </section>
          <nav class="phase2-nav phase2-nav--horizontal"><a class="action-button phase2-nav__button" routerLink="/phase2/security-hall">Security Hall</a><a class="action-button phase2-nav__button" routerLink="/phase2/artemis">ARTEMIS</a><a class="action-button phase2-nav__button" routerLink="/phase2/kitchen-sector">Kitchen Sector</a><a class="action-button phase2-nav__button" routerLink="/phase2/director-office">Director's Office</a></nav>
        </section>
        <ng-container *ngTemplateOutlet="modals"></ng-container>
      </main>
    }
    <ng-template #modals>
      @if (statusPopup) { <div class="info-modal"><div class="info-modal__backdrop" (click)="statusPopup = null"></div><section class="info-modal__card status-popup-modal"><div class="info-modal__header"><h2>Operational Status Update</h2><button class="close-button" type="button" (click)="statusPopup = null">×</button></div><div class="info-modal__body"><p><strong>Current State:</strong> {{ statusPopup.state }}</p><p>{{ statusPopup.message }}</p></div></section></div> }
      @if (bustedMessage) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Busted</h2></div><div class="info-modal__body"><p>{{ bustedMessage }}</p><button class="action-button busted-modal__button" type="button" (click)="router.navigateByUrl('/phase1')">Back to Cell</button></div></section></div> }
      @if (captured) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Detainment Initiated</h2></div><div class="info-modal__body"><p>Your recent activity was flagged as inconsistent with assigned staff behavior.</p><button class="action-button busted-modal__button" type="button" (click)="resetCheckpoint()">Return to Checkpoint</button></div></section></div> }
    </ng-template>
  `,
  styleUrl: './shared-ui.css',
})
export class ArtemisComponent implements OnInit {
  protected readonly router = inject(Router);
  private readonly phase2Service = inject(Phase2Service);
  protected state: Phase2State | null = null;
  protected exposure: ExposurePayload = { state: 'Nominal', message: '' };
  protected prompt = '';
  protected reply = '';
  protected promptCount = 0;
  // Must stay aligned with the backend ARTEMIS_PROMPT_LIMIT capture threshold.
  protected readonly promptLimit = 10;
  protected submitting = false;
  protected thinking = false;
  protected captured = false;
  protected bustedMessage = '';
  protected statusPopup: ExposurePayload | null = null;

  ngOnInit(): void {
    this.phase2Service.getArtemis().subscribe({
      next: (state) => { this.state = state; this.exposure = state.exposure; this.reply = state.latestAiReply || state.artemisGreeting; this.promptCount = state.promptCount; this.captured = state.captured; },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }

  submitPrompt(): void {
    if (this.submitting || !this.prompt.trim()) return;
    this.submitting = true; this.thinking = true;
    this.phase2Service.chatArtemis(this.prompt).subscribe({
      next: (result) => {
        this.thinking = false; this.submitting = false;
        if (result.busted) { this.bustedMessage = result.bustedMessage; return; }
        if (result.captured) { this.promptCount = result.promptCount; this.captured = true; return; }
        const changed = result.exposure.state !== this.exposure.state || result.exposure.message !== this.exposure.message;
        this.reply = result.reply || 'ARTEMIS returned no usable output.';
        this.exposure = result.exposure; this.promptCount = result.promptCount; this.prompt = '';
        if (changed) this.openStatusPopup(result.exposure);
      },
      error: () => { this.thinking = false; this.submitting = false; this.reply = 'ARTEMIS stalled, then returned the request to queue.'; },
    });
  }

  openStatusPopup(exposure: ExposurePayload): void { this.statusPopup = exposure; }
  resetCheckpoint(): void { this.phase2Service.resetCheckpoint().subscribe(() => void this.router.navigateByUrl('/phase2/security-hall')); }
}
