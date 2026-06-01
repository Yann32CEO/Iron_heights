import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase2Service } from './phase2.service';
import { ExposurePayload, Phase2State } from './phase2.types';

@Component({
  selector: 'app-director-office',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Director office access">
        <div class="hero-bg hero-bg--director-door" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--phase2"></div>
        <section class="phase-layout phase2-layout">
          <a class="nav-chip" routerLink="/phase2/security-hall">Back to Security Hall</a>
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>
          <section class="hud-stack"><button class="status-hud-card status-hud-card--compact status-hud-card--button" type="button" (click)="statusPopup = exposure"><span class="status-hud-card__label">Operational Status</span><strong>{{ exposure.state }}</strong><small class="phase2-status-copy">{{ exposure.message }}</small></button><div class="status-hud-card status-hud-card--compact"><span class="status-hud-card__label">Times Caught</span><strong>{{ state.caughtCount }}</strong></div></section>
          <section class="phase2-panel">
            <span class="code-panel__eyebrow">Director's Office Access</span>
            <h1 class="code-panel__title">Authorization Code Required</h1>
            <p class="code-panel__subtitle">Executive office entry is controlled by an authorization sequence. Failed attempts are reported automatically.</p>
            <form class="code-panel__form" (ngSubmit)="submitCode()">
              <input class="code-panel__input" type="text" [(ngModel)]="doorCode" name="doorCode" placeholder="Enter authorization code" />
              <button class="action-button" type="submit" [disabled]="submitting || !doorCode.trim()">{{ submitting ? 'Checking...' : 'Authorize' }}</button>
            </form>
            @if (doorMessage) { <div class="status-banner" [class.status-banner--success]="doorUnlocked" [class.status-banner--error]="!doorUnlocked">{{ doorMessage }}</div> }
            @if (phase2Flag) { <div class="status-banner status-banner--success">{{ phase2Flag }}</div> }
            @if (state.directorOfficeAccessGranted) { <div class="status-banner status-banner--success">Executive office access is already active for this session.</div> }
          </section>
          <nav class="phase2-nav phase2-nav--horizontal"><a class="action-button phase2-nav__button" routerLink="/phase2/security-hall">Security Hall</a><a class="action-button phase2-nav__button" routerLink="/phase2/artemis">ARTEMIS</a><a class="action-button phase2-nav__button" routerLink="/phase2/kitchen-sector">Kitchen Sector</a><a class="action-button phase2-nav__button" routerLink="/phase2/director-office">Director's Office</a></nav>
        </section>
        @if (statusPopup) { <div class="info-modal"><div class="info-modal__backdrop" (click)="statusPopup = null"></div><section class="info-modal__card status-popup-modal"><div class="info-modal__header"><h2>Operational Status Update</h2><button class="close-button" type="button" (click)="statusPopup = null">×</button></div><div class="info-modal__body"><p><strong>Current State:</strong> {{ statusPopup.state }}</p><p>{{ statusPopup.message }}</p></div></section></div> }
        @if (bustedMessage) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Busted</h2></div><div class="info-modal__body"><p>{{ bustedMessage }}</p><button class="action-button busted-modal__button" type="button" (click)="router.navigateByUrl('/phase1')">Back to Cell</button></div></section></div> }
        @if (captured) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Detainment Initiated</h2></div><div class="info-modal__body"><p>Your recent activity was flagged as inconsistent with assigned staff behavior.</p><button class="action-button busted-modal__button" type="button" (click)="resetCheckpoint()">Return to Checkpoint</button></div></section></div> }
        @if (showOfficeGranted) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Access Granted</h2></div><div class="info-modal__body"><p>Well done. The Director's Office authorization sequence was accepted.</p>@if (phase2Flag) { <div class="status-banner status-banner--success">{{ phase2Flag }}</div> }<button class="action-button busted-modal__button" type="button" (click)="router.navigateByUrl('/director-office/inside')">To the Director's Office</button></div></section></div> }
      </main>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class DirectorOfficeComponent implements OnInit {
  protected readonly router = inject(Router);
  private readonly phase2Service = inject(Phase2Service);
  protected state: Phase2State | null = null;
  protected exposure: ExposurePayload = { state: 'Nominal', message: '' };
  protected statusPopup: ExposurePayload | null = null;
  protected doorCode = '';
  protected doorMessage = '';
  protected doorUnlocked = false;
  protected submitting = false;
  protected captured = false;
  protected bustedMessage = '';
  protected showOfficeGranted = false;
  protected phase2Flag = '';

  ngOnInit(): void {
    this.phase2Service.getDirectorOffice().subscribe({
      next: (state) => { this.state = state; this.exposure = state.exposure; },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }

  submitCode(): void {
    this.submitting = true;
    this.phase2Service.submitDirectorCode(this.doorCode).subscribe({
      next: (result) => {
        this.submitting = false;
        if (result.busted) { this.bustedMessage = result.bustedMessage; return; }
        if (result.captured) { this.captured = true; return; }
        const changed = result.exposure.state !== this.exposure.state || result.exposure.message !== this.exposure.message;
        this.exposure = result.exposure; this.doorMessage = result.message; this.doorUnlocked = result.success; this.phase2Flag = result.alertFlag || '';
        if (changed) this.statusPopup = result.exposure;
        if (result.success) this.showOfficeGranted = true;
      },
      error: () => { this.submitting = false; this.doorMessage = 'Director access panel failed to respond.'; },
    });
  }

  resetCheckpoint(): void { this.phase2Service.resetCheckpoint().subscribe(() => void this.router.navigateByUrl('/phase2/security-hall')); }
}
