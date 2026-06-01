import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase3Service } from './phase3.service';
import { DirectorOfficeInsideState } from './phase3.types';

@Component({
  selector: 'app-director-office-inside',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Director office interior">
        <div class="hero-bg hero-bg--director-office-inside" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--office"></div>
        <section class="phase-layout director-office-layout">
          <a class="nav-chip" routerLink="/phase2/director-office">Back to Office Door</a>
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>
          <section class="hud-stack"><div class="status-hud-card status-hud-card--compact"><span class="status-hud-card__label">Times Caught</span><strong>{{ state.caughtCount }}</strong></div></section>
          <button class="action-button action-button--ghost director-office-button director-office-button--roof" type="button" (click)="showRoof = true">Open</button>
          <button class="action-button action-button--ghost director-office-button director-office-button--diary" type="button" (click)="goDiary()" [disabled]="checkingDiary">{{ checkingDiary ? 'Checking...' : 'Diary' }}</button>
          <div class="utility-zone utility-zone--left"><button class="action-button action-button--ghost" type="button" (click)="showLetter = true">Message</button></div>
          <div class="utility-zone utility-zone--right utility-zone--stacked"><button class="action-button action-button--ghost" type="button" (click)="resyncRelay()" [disabled]="syncing">{{ syncing ? 'Re-syncing...' : 'Re-sync' }}</button><button class="action-button action-button--ghost" type="button" (click)="showIntercept = true">Info</button></div>
        </section>

        @if (showLetter) {
          <div class="info-modal"><div class="info-modal__backdrop" (click)="showLetter = false"></div><section class="info-modal__card info-modal__card--wide"><div class="info-modal__header"><h2>Director Letter</h2><button class="close-button" type="button" (click)="showLetter = false">×</button></div><div class="info-modal__body"><pre class="phase3-pre">{{ state.directorLetter }}</pre></div></section></div>
        }
        @if (showIntercept) {
          <div class="info-modal"><div class="info-modal__backdrop" (click)="showIntercept = false"></div><section class="info-modal__card info-modal__card--wide"><div class="info-modal__header"><h2>Access Intercept</h2><button class="close-button" type="button" (click)="showIntercept = false">×</button></div><div class="info-modal__body"><pre class="phase3-pre">{{ interceptJson }}</pre></div></section></div>
        }
        @if (showRoof) {
          <div class="info-modal"><div class="info-modal__backdrop" (click)="showRoof = false"></div><section class="info-modal__card"><div class="info-modal__header"><h2>Roof Access</h2><button class="close-button" type="button" (click)="showRoof = false">×</button></div><div class="info-modal__body"><form class="code-panel__form phase3-modal-form" (ngSubmit)="submitRoofCode()"><input class="code-panel__input" type="text" [(ngModel)]="roofCode" name="roofCode" placeholder="Enter roof access code" /><button class="action-button" type="submit" [disabled]="checkingRoof || !roofCode.trim()">{{ checkingRoof ? 'Checking...' : 'Open' }}</button></form>@if (roofMessage) { <div class="status-banner" [class.status-banner--success]="roofUnlocked" [class.status-banner--error]="!roofUnlocked">{{ roofMessage }}</div> }@if (roofFlag) { <div class="status-banner status-banner--success">{{ roofFlag }}</div> }</div></section></div>
        }
        @if (showRoofAward) {
          <div class="info-modal info-modal--priority" role="dialog" aria-modal="true" aria-label="Roof access awarded">
            <div class="info-modal__backdrop"></div>
            <section class="info-modal__card">
              <div class="info-modal__header">
                <h2>Roof Access Accepted</h2>
              </div>
              <div class="info-modal__body">
                <p>{{ roofMessage }}</p>
                @if (roofFlag) {
                  <div class="status-banner status-banner--success">{{ roofFlag }}</div>
                }
                <button class="action-button busted-modal__button" type="button" (click)="openSnarkScene()">To the roof</button>
              </div>
            </section>
          </div>
        }
        @if (showSnark) {
          <div class="info-modal info-modal--priority" role="dialog" aria-modal="true" aria-label="SNARK inspection">
            <div class="info-modal__backdrop"></div>
            <section class="info-modal__card info-modal__card--wide snark-modal">
              <div class="info-modal__header">
                <h2>SNARK</h2>
              </div>
              <div class="info-modal__body snark-chatbox">
                <p class="snark-chatbox__subtitle">Sarcastic Neural Assistant for Routine Knowledge</p>
                <div class="snark-chatbox__messages">
                  <div class="snark-chatbox__message snark-chatbox__message--snark">
                    <span class="snark-chatbox__author">SNARK</span>
                    <p>External roof authorization is blocked by inspection.</p>
                  </div>
                  <div class="snark-chatbox__message snark-chatbox__message--snark">
                    <span class="snark-chatbox__author">SNARK</span>
                    <p>Declared length and streamed inspection records do not agree. Roof clearance remains internal.</p>
                  </div>
                </div>
                <div class="phase2-inline-actions">
                  <button class="action-button" type="button" (click)="goFinale()" [disabled]="!state.roofAccessGranted || checkingFinale">
                    To the roof
                  </button>
                </div>
              </div>
            </section>
          </div>
        }
        @if (relayMessage) {
          <div class="info-modal"><div class="info-modal__backdrop" (click)="relayMessage = ''"></div><section class="info-modal__card status-popup-modal"><div class="info-modal__header"><h2>Relay Re-sync</h2><button class="close-button" type="button" (click)="relayMessage = ''">×</button></div><div class="info-modal__body"><p class="status-banner" [class.status-banner--success]="relayAccepted" [class.status-banner--error]="!relayAccepted">{{ relayMessage }}</p></div></section></div>
        }
        @if (showDiaryDenied) {
          <div class="info-modal"><div class="info-modal__backdrop" (click)="showDiaryDenied = false"></div><section class="info-modal__card"><div class="info-modal__header"><h2>Diary Access</h2><button class="close-button" type="button" (click)="showDiaryDenied = false">×</button></div><div class="info-modal__body"><p>Only the Director can access this diary.</p></div></section></div>
        }
      </main>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class DirectorOfficeInsideComponent implements OnInit {
  // This component surfaces Phase 3 clues only; backend remains authoritative for relay and roof unlocks.
  protected readonly router = inject(Router);
  private readonly phase3Service = inject(Phase3Service);
  protected state: DirectorOfficeInsideState | null = null;
  protected showLetter = false;
  protected showIntercept = false;
  protected showRoof = false;
  protected syncing = false;
  protected relayMessage = '';
  protected relayAccepted = false;
  protected roofCode = '';
  protected roofMessage = '';
  protected roofFlag = '';
  protected roofUnlocked = false;
  protected checkingRoof = false;
  protected checkingDiary = false;
  protected checkingFinale = false;
  protected showDiaryDenied = false;
  protected showSnark = false;
  protected showRoofAward = false;

  get interceptJson(): string {
    return this.state ? JSON.stringify(this.state.intercept, null, 2) : '';
  }

  ngOnInit(): void {
    this.phase3Service.getDirectorOfficeInside().subscribe({
      next: (state) => {
        this.state = state;
        this.relayAccepted = state.directorJwtAccepted;
        this.showSnark = state.roofCodeAccepted;
      },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }

  resyncRelay(): void {
    this.syncing = true;
    this.phase3Service.resyncDirectorRelay().subscribe({
      next: (result) => {
        this.syncing = false;
        this.relayMessage = result.message;
        this.relayAccepted = result.success;
        if (this.state) this.state = { ...this.state, role: result.role, directorJwtAccepted: result.directorJwtAccepted, directorDiaryUnlocked: result.directorDiaryUnlocked };
        if (result.alertFlag) this.relayMessage = `${result.message} ${result.alertFlag}`;
      },
      error: () => { this.syncing = false; this.relayMessage = 'Executive relay service failed to respond.'; this.relayAccepted = false; },
    });
  }

  goDiary(): void {
    this.checkingDiary = true;
    this.phase3Service.getDirectorDiary().subscribe({
      next: () => { this.checkingDiary = false; void this.router.navigateByUrl('/phase3/director-diary'); },
      error: (error) => {
        this.checkingDiary = false;
        if (isForbiddenError(error)) { this.showDiaryDenied = true; return; }
        this.relayMessage = 'Diary service failed to respond.';
        this.relayAccepted = false;
      },
    });
  }

  submitRoofCode(): void {
    this.checkingRoof = true;
    this.phase3Service.submitRoofCode(this.roofCode).subscribe({
      next: (result) => {
        this.checkingRoof = false;
        this.roofMessage = result.message;
        this.roofUnlocked = result.success;
        this.roofFlag = result.alertFlag || '';
        if (this.state) this.state = { ...this.state, roofCodeAccepted: result.roofCodeAccepted, roofAccessGranted: result.roofAccessGranted };
        if (result.success) {
          this.showRoof = false;
          this.showRoofAward = true;
        }
      },
      error: (error) => {
        this.checkingRoof = false;
        if (isForbiddenError(error)) void this.router.navigateByUrl('/403');
        else this.roofMessage = 'Roof access service failed to respond.';
      },
    });
  }

  openSnarkScene(): void {
    this.showRoofAward = false;
    this.showSnark = true;
  }

  goFinale(): void {
    if (!this.state?.roofAccessGranted || this.checkingFinale) return;
    this.checkingFinale = true;
    this.phase3Service.getFinale().subscribe({
      next: () => { this.checkingFinale = false; void this.router.navigateByUrl('/phase3/finale'); },
      error: (error) => {
        this.checkingFinale = false;
        if (isForbiddenError(error)) void this.router.navigateByUrl('/403');
      },
    });
  }
}
