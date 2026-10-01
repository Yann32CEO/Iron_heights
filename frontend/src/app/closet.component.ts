import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { ChangingRoomService } from './changing-room.service';
import { ClosetState } from './changing-room.types';
import { CorridorService } from './corridor.service';
import { startEscapeCountdown } from './countdown.util';
import { isCaughtError, isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';

@Component({
  selector: 'app-closet',
  standalone: true,
  imports: [CommonModule, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Iron Heights uniform closet">
        <div class="hero-bg hero-bg--closet" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--changing-room"></div>

        <section class="phase-layout changing-room-layout">
          <div class="door-locked-chip" aria-label="Closet access state">Locker Access Granted</div>

          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>

          <section class="scene-copy scene-copy--closet" aria-label="Closet scene note">
            <span class="scene-copy__eyebrow">Phase 1 · Uniform Storage</span>
            <p class="scene-copy__body">One clean uniform is all it takes to stop looking like prey and start moving like staff.</p>
          </section>

          <section class="changing-room-actions" aria-label="Closet controls">
            <button class="action-button changing-room-actions__button" type="button" (click)="pickUniform()">Pick a Uniform</button>
          </section>

          <section class="hud-stack" aria-label="Closet status panels">
            @if (!state.timerDisabled && !uniformCollected) {
              <div class="status-hud-card status-hud-card--timer" aria-label="Countdown timer">
              <span class="status-hud-card__label">Countdown</span>
              <strong>{{ remainingTime }}</strong>
              </div>
            }
            <div class="status-hud-card" aria-label="Times caught counter">
              <span class="status-hud-card__label">Times Caught</span>
              <strong>{{ state.caughtCount }}</strong>
            </div>
          </section>
        </section>
      </main>
    }

    @if (showBusted) {
      <div class="info-modal info-modal--priority" role="dialog" aria-modal="true" aria-label="Guard alert">
        <div class="info-modal__backdrop"></div>
        <section class="info-modal__card busted-modal">
          <div class="info-modal__header"><h2>Busted</h2></div>
          <div class="info-modal__body">
            <p>You ran out of time before the disguise was in your hands. The search pattern closes and the block drags you back to square one.</p>
            <button class="action-button busted-modal__button" type="button" (click)="backToCell()">Back to Cell</button>
          </div>
        </section>
      </div>
    }

    @if (uniformCollected) {
      <div class="info-modal info-modal--priority" role="dialog" aria-modal="true" aria-label="Uniform collected">
        <div class="info-modal__backdrop"></div>
        <section class="info-modal__card changing-room-modal">
          <div class="info-modal__header"><h2>Uniform Collected</h2></div>
            <div class="info-modal__body">
              <p>The uniform fits well enough to fool a glance. From here on, Iron Heights will read you as staff until you give it a reason not to.</p>
              <p><strong>Flag:</strong> <code>{{ collectedFlag }}</code></p>
              <button class="action-button busted-modal__button" type="button" (click)="goToPhase2()">Go to Security Hall</button>
            </div>
          </section>
        </div>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class ClosetComponent implements OnInit, OnDestroy {
  private readonly changingRoomService = inject(ChangingRoomService);
  private readonly corridorService = inject(CorridorService);
  private readonly router = inject(Router);

  protected state: ClosetState | null = null;
  protected remainingTime = '01:30';
  protected showBusted = false;
  protected uniformCollected = false;
  protected collectedFlag = '';

  private countdownSubscription?: Subscription;
  private timeoutResolving = false;

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
  }

  protected pickUniform(): void {
    this.changingRoomService.pickUniform().subscribe({
      next: (state) => this.applyState(state),
      error: (error) => this.handleError(error),
    });
  }

  protected backToCell(): void {
    this.corridorService.returnToCell().subscribe({
      next: () => void this.router.navigateByUrl('/phase1'),
      error: (error) => this.handleError(error),
    });
  }

  protected goToPhase2(): void {
    void this.router.navigateByUrl('/phase2/security-hall');
  }

  private load(): void {
    this.changingRoomService.getCloset().subscribe({
      next: (state) => this.applyState(state),
      error: (error) => this.handleError(error),
    });
  }

  private applyState(state: ClosetState): void {
    this.state = state;
    // A reload after the pickup comes back as collected, so the flag modal is shown again.
    this.uniformCollected = state.uniformCollected;
    this.collectedFlag = state.flag ?? '';
    this.countdownSubscription?.unsubscribe();
    if (state.timerDisabled || state.uniformCollected) {
      return;
    }
    this.countdownSubscription = startEscapeCountdown(
      state.remainingMs,
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
