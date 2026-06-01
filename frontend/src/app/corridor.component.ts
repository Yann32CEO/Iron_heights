import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription, interval } from 'rxjs';

import { CorridorService } from './corridor.service';
import { formatRemainingMs, getRemainingMs } from './countdown.util';
import { CorridorState } from './corridor.types';
import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';

@Component({
  selector: 'app-corridor',
  standalone: true,
  imports: [CommonModule, PlayerProfileButtonComponent],
  template: `
    @if (corridorState) {
      <main class="hero-shell" aria-label="Iron Heights guarded corridor">
        <div class="hero-bg hero-bg--corridor" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--corridor"></div>

        <section class="phase-layout corridor-layout">
          <app-player-profile-button [alias]="corridorState.alias" [role]="corridorState.role"></app-player-profile-button>

          <section class="corridor-buttons" aria-label="Corridor entry points">
            <button class="action-button corridor-door-button corridor-door-button--left" type="button" (click)="enterYard()">Enter</button>
            <button class="action-button corridor-door-button corridor-door-button--center" type="button" (click)="tryKitchen()">Enter</button>
            <button class="action-button corridor-door-button corridor-door-button--right" type="button" (click)="enterChangingRoom()">Enter</button>
          </section>

          <section class="hud-stack" aria-label="Corridor status panels">
            <div class="status-hud-card status-hud-card--timer" aria-label="Countdown timer">
              <span class="status-hud-card__label">Countdown</span>
              <strong>{{ remainingTime }}</strong>
            </div>
            <div class="status-hud-card" aria-label="Times caught counter">
              <span class="status-hud-card__label">Times Caught</span>
              <strong>{{ corridorState.caughtCount }}</strong>
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

    @if (showKitchenDenied) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Kitchen access denied">
        <div class="info-modal__backdrop" (click)="showKitchenDenied = false"></div>
        <section class="info-modal__card busted-modal">
          <div class="info-modal__header">
            <h2>Kitchen Access Denied</h2>
            <button class="close-button" type="button" (click)="showKitchenDenied = false">×</button>
          </div>
          <div class="info-modal__body">
            <p>The kitchen stays sealed after lights-out. Only Guards and Directors are cleared to pass through this door.</p>
          </div>
        </section>
      </div>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class CorridorComponent implements OnInit, OnDestroy {
  private readonly corridorService = inject(CorridorService);
  private readonly router = inject(Router);

  protected corridorState: CorridorState | null = null;
  protected remainingTime = '01:30';
  protected showBusted = false;
  protected showKitchenDenied = false;

  private countdownSubscription?: Subscription;
  private timeoutResolving = false;

  ngOnInit(): void {
    this.corridorService.getCorridor().subscribe({
      next: (state) => {
        this.corridorState = state;
        this.startCountdown(state.escapedAt);
      },
      error: (error) => {
        if (isForbiddenError(error)) {
          this.corridorService.leaveYard().subscribe({
            next: () => void this.router.navigateByUrl('/phase1/corridor'),
            error: () => void this.router.navigateByUrl('/403'),
          });
        }
      },
    });
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
  }

  protected enterYard(): void {
    this.corridorService.enterYard().subscribe({
      next: () => void this.router.navigateByUrl('/phase1/yard'),
      error: (error) => this.handleForbidden(error),
    });
  }

  protected tryKitchen(): void {
    this.corridorService.tryKitchen().subscribe({
      next: (response) => {
        this.showKitchenDenied = !response.allowed && response.kitchenDenied;
      },
      error: (error) => this.handleForbidden(error),
    });
  }

  protected enterChangingRoom(): void {
    this.corridorService.enterChangingRoom().subscribe({
      next: () => void this.router.navigateByUrl('/phase1/changing-room'),
      error: (error) => this.handleForbidden(error),
    });
  }

  protected backToCell(): void {
    this.corridorService.returnToCell().subscribe({
      next: () => void this.router.navigateByUrl('/phase1'),
      error: (error) => this.handleForbidden(error),
    });
  }

  private startCountdown(escapedAt: string | null): void {
    this.countdownSubscription?.unsubscribe();
    this.remainingTime = formatRemainingMs(getRemainingMs(escapedAt));
    this.countdownSubscription = interval(1000).subscribe(() => {
      const remainingMs = getRemainingMs(escapedAt);
      this.remainingTime = formatRemainingMs(remainingMs);
      if (remainingMs <= 0) {
        this.countdownSubscription?.unsubscribe();
        this.resolveTimeout();
      }
    });
  }

  private resolveTimeout(): void {
    if (this.timeoutResolving) return;
    this.timeoutResolving = true;
    this.corridorService.resolveTimeout().subscribe({
      next: (result) => {
        this.timeoutResolving = false;
        if (result.caught) {
          this.showBusted = true;
          return;
        }
        void this.router.navigateByUrl('/phase1/corridor');
      },
      error: (error) => {
        this.timeoutResolving = false;
        this.handleForbidden(error);
      },
    });
  }

  private handleForbidden(error: { status?: number }): void {
    if (isForbiddenError(error)) {
      void this.router.navigateByUrl('/403');
    }
  }
}
