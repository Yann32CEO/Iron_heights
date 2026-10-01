import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { CorridorService } from './corridor.service';
import { startEscapeCountdown } from './countdown.util';
import { CorridorState } from './corridor.types';
import { isCaughtError, isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';

@Component({
  selector: 'app-yard',
  standalone: true,
  imports: [CommonModule, PlayerProfileButtonComponent],
  template: `
    @if (yardState) {
      <main class="hero-shell" aria-label="Iron Heights yard">
        <div class="hero-bg hero-bg--yard" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase"></div>

        <section class="phase-layout yard-layout">
          <button class="action-button nav-chip" type="button" (click)="leaveYard()">Go-back</button>

          <section class="scene-copy scene-copy--yard" aria-label="Yard scene note">
            <span class="scene-copy__eyebrow">Phase 1 · Outer Yard</span>
            <p class="scene-copy__body">Cold air, watchtowers, and too much open ground. Out here, hesitation is as dangerous as noise.</p>
          </section>

          <app-player-profile-button [alias]="yardState.alias" [role]="yardState.role"></app-player-profile-button>

          <section class="hud-stack" aria-label="Yard status panels">
            <div class="status-hud-card status-hud-card--timer" aria-label="Countdown timer">
              <span class="status-hud-card__label">Countdown</span>
              <strong>{{ remainingTime }}</strong>
            </div>
            <div class="status-hud-card" aria-label="Times caught counter">
              <span class="status-hud-card__label">Times Caught</span>
              <strong>{{ yardState.caughtCount }}</strong>
            </div>
          </section>
        </section>
      </main>
    }

    @if (showBusted) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Guard alert">
        <div class="info-modal__backdrop"></div>
        <section class="info-modal__card busted-modal">
          <div class="info-modal__header"><h2>Busted</h2></div>
          <div class="info-modal__body">
            <p>The countdown died before you disappeared. Sirens rise, boots close in, and the block takes you back.</p>
            <button class="action-button busted-modal__button" type="button" (click)="backToCell()">Back to Cell</button>
          </div>
        </section>
      </div>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class YardComponent implements OnInit, OnDestroy {
  private readonly corridorService = inject(CorridorService);
  private readonly router = inject(Router);

  protected yardState: CorridorState | null = null;
  protected remainingTime = '01:30';
  protected showBusted = false;

  private countdownSubscription?: Subscription;
  private timeoutResolving = false;

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
  }

  protected leaveYard(): void {
    this.corridorService.leaveYard().subscribe({
      next: (state) => {
        if (state.scene === 'corridor') {
          void this.router.navigateByUrl('/phase1/corridor');
          return;
        }

        if (state.scene === 'yard') {
          return;
        }

        void this.router.navigateByUrl('/403');
      },
      error: (error) => this.handleError(error),
    });
  }

  protected backToCell(): void {
    this.corridorService.returnToCell().subscribe({
      next: () => void this.router.navigateByUrl('/phase1'),
      error: (error) => this.handleError(error),
    });
  }

  private load(): void {
    this.corridorService.getYard().subscribe({
      next: (state) => {
        this.yardState = state;
        this.startCountdown(state.remainingMs);
      },
      error: (error) => this.handleError(error),
    });
  }

  private startCountdown(remainingMs: number | null): void {
    this.countdownSubscription?.unsubscribe();
    this.countdownSubscription = startEscapeCountdown(
      remainingMs,
      (label) => (this.remainingTime = label),
      () => this.resolveTimeout(),
    );
  }

  private resolveTimeout(): void {
    if (this.timeoutResolving) return;
    this.timeoutResolving = true;
    this.corridorService.resolveTimeout().subscribe({
      next: (result) => {
        this.timeoutResolving = false;
        if (result.caught) {
          this.bust();
          return;
        }
        // The server still sees time left: resync with its remaining time instead of stalling at 00:00.
        this.load();
      },
      error: (error) => {
        this.timeoutResolving = false;
        this.handleError(error);
      },
    });
  }

  private bust(): void {
    this.countdownSubscription?.unsubscribe();
    this.showBusted = true;
  }

  private handleError(error: { status?: number }): void {
    if (isCaughtError(error)) {
      this.bust();
      return;
    }
    if (isForbiddenError(error)) {
      void this.router.navigateByUrl('/403');
    }
  }
}
