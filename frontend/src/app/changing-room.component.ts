import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription, interval } from 'rxjs';

import { ChangingRoomService } from './changing-room.service';
import { ChangingRoomState } from './changing-room.types';
import { formatRemainingMs, getRemainingMs } from './countdown.util';
import { CorridorService } from './corridor.service';
import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';

@Component({
  selector: 'app-changing-room',
  standalone: true,
  imports: [CommonModule, FormsModule, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Iron Heights changing room">
        <div class="hero-bg hero-bg--changing-room" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--changing-room"></div>

        <section class="phase-layout changing-room-layout">
          <div class="door-locked-chip" aria-label="Changing room door state">Door Locked</div>
          <div class="door-warning-bar" aria-label="Changing room point of no return">Door locked. No turning back from now</div>

          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>

          <section class="changing-room-actions" aria-label="Changing room controls">
            <button class="action-button changing-room-actions__button" type="button" (click)="requestUniform()">
              {{ hasTemporaryBadge || state.role === 'Guard' ? 'Get New Uniform' : 'Get a Uniform' }}
            </button>
            <button class="action-button action-button--ghost changing-room-actions__button" type="button" (click)="showLostBadge = true">
              Lost Badge?
            </button>
          </section>

          <button class="action-button action-button--ghost inspect-board-button" type="button" (click)="showInspectNotice = true">Inspect</button>
          <button class="action-button action-button--ghost inspect-clothes-button" type="button" (click)="showInspectClothes = true">Inspect</button>

          <section class="hud-stack" aria-label="Changing room status panels">
            <div class="status-hud-card status-hud-card--timer" aria-label="Countdown timer">
              <span class="status-hud-card__label">Countdown</span>
              <strong>{{ remainingTime }}</strong>
            </div>
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
            <p>You stayed inside the window too long. The corridor locks down, the hunt begins, and the facility sends you back to the cell.</p>
            <button class="action-button busted-modal__button" type="button" (click)="backToCell()">Back to Cell</button>
          </div>
        </section>
      </div>
    }

    @if (showUniformDenied) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Changing room access denied">
        <div class="info-modal__backdrop" (click)="showUniformDenied = false"></div>
        <section class="info-modal__card busted-modal">
          <div class="info-modal__header">
            <h2>Uniform Access Denied</h2>
            <button class="close-button" type="button" (click)="showUniformDenied = false">×</button>
          </div>
          <div class="info-modal__body">
            <p>No badge, no uniform. The staff lockers stay closed until the system sees valid credentials.</p>
          </div>
        </section>
      </div>
    }

    @if (showLostBadge) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Night shift temporary badge request">
        <div class="info-modal__backdrop" (click)="showLostBadge = false"></div>
        <section class="info-modal__card changing-room-modal">
          <div class="info-modal__header">
            <h2>Night Shift Temporary Badge</h2>
            <button class="close-button" type="button" (click)="showLostBadge = false">×</button>
          </div>
          <div class="info-modal__body">
            <p>Night shift staff can request a temporary badge through staged verification. Start with the guard name. If the checkpoint opens, the Guard ID field will be released for final verification.</p>
            <div class="changing-room-form">
              <input class="code-panel__input" type="text" [(ngModel)]="guardNameInput" name="guardName" placeholder="Guard Name" autocomplete="off" />
              @if (lostBadgeStage === 'guard-id') {
                <input class="code-panel__input" type="text" [(ngModel)]="guardIdInput" name="guardId" placeholder="Guard ID" autocomplete="off" />
              }
              <button class="action-button" type="button" [disabled]="submittingBadge" (click)="submitLostBadge()">
                {{ submittingBadge ? 'Requesting...' : lostBadgeStage === 'guard-id' ? 'Verify Guard ID' : 'Open Verification Checkpoint' }}
              </button>
            </div>
            @if (badgeMessage) {
              <p class="status-banner changing-room-form__status" [class.status-banner--success]="badgeVariant === 'success'" [class.status-banner--error]="badgeVariant !== 'success'">{{ badgeMessage }}</p>
            }
          </div>
        </section>
      </div>
    }

    @if (showInspectNotice) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Laundry notice inspection">
        <div class="info-modal__backdrop" (click)="showInspectNotice = false"></div>
        <section class="info-modal__card changing-room-modal inspect-notice-modal">
          <div class="info-modal__header">
            <h2>Night Laundry Pickup</h2>
            <button class="close-button" type="button" (click)="showInspectNotice = false">×</button>
          </div>
          <div class="info-modal__body">
            <img class="inspect-notice-modal__image" src="/assets/notice.png" alt="Night Laundry Pickup notice" />
            <p class="inspect-notice-modal__message">
              47, whatever was printed here did not survive the night. Luckily, you can obtain it
              <a class="inspect-notice-modal__link" href="/assets/notice.png" download>here</a>.
            </p>
          </div>
        </section>
      </div>
    }

    @if (showInspectClothes) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Clothes pile inspection">
        <div class="info-modal__backdrop" (click)="showInspectClothes = false"></div>
        <section class="info-modal__card changing-room-modal inspect-claims-modal">
          <div class="info-modal__header">
            <h2>uniform_claims</h2>
            <button class="close-button" type="button" (click)="showInspectClothes = false">×</button>
          </div>
          <div class="info-modal__body">
            <div class="claims-form">
              <div class="claims-form__controls">
                <label class="claims-form__label" for="claims-filter-field">Filter</label>
                <select id="claims-filter-field" class="code-panel__input claims-form__select" [(ngModel)]="claimsFilterField" name="claimsFilterField">
                  <option value="guard_id">guard_id</option>
                  <option value="guard_name">guard_name</option>
                  <option value="locker">locker</option>
                  <option value="shift">shift</option>
                  <option value="uniform_size">uniform_size</option>
                  <option value="fabric_type">fabric_type</option>
                  <option value="wash_cycle">wash_cycle</option>
                </select>
              </div>
              <input class="code-panel__input" type="text" [(ngModel)]="claimsFilterValue" name="claimsFilterValue" placeholder="Filter value" autocomplete="off" />
              <button class="action-button" type="button" [disabled]="submittingClaims" (click)="submitUniformClaims()">
                {{ submittingClaims ? 'Searching...' : 'Search' }}
              </button>
            </div>
            <div class="status-banner changing-room-form__status status-banner--error claims-result-box">{{ claimsMessage || 'Only guards are allowed to use the search function.' }}</div>
          </div>
        </section>
      </div>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class ChangingRoomComponent implements OnInit, OnDestroy {
  private readonly changingRoomService = inject(ChangingRoomService);
  private readonly corridorService = inject(CorridorService);
  private readonly router = inject(Router);

  protected state: ChangingRoomState | null = null;
  protected remainingTime = '01:30';
  protected showBusted = false;
  protected showUniformDenied = false;
  protected showLostBadge = false;
  protected showInspectNotice = false;
  protected showInspectClothes = false;
  protected hasTemporaryBadge = false;
  protected badgeMessage = '';
  protected badgeVariant = 'error';
  protected lostBadgeStage = 'guard-name';
  protected guardNameInput = '';
  protected guardIdInput = '';
  protected claimsFilterField = 'guard_name';
  protected claimsFilterValue = '';
  protected claimsMessage = '';
  protected submittingBadge = false;
  protected submittingClaims = false;

  private countdownSubscription?: Subscription;
  private timeoutResolving = false;

  ngOnInit(): void {
    this.changingRoomService.getChangingRoom().subscribe({
      next: (state) => {
        this.state = state;
        this.showUniformDenied = state.uniformDenied;
        this.hasTemporaryBadge = state.temporaryBadgeIssued;
        this.badgeMessage = state.lostBadgeMessage;
        this.badgeVariant = state.lostBadgeVariant || 'error';
        this.showLostBadge = Boolean(state.lostBadgeMessage);
        this.startCountdown(state.escapedAt);
      },
      error: (error) => this.handleForbidden(error),
    });
  }

  ngOnDestroy(): void {
    this.countdownSubscription?.unsubscribe();
  }

  protected requestUniform(): void {
    this.changingRoomService.requestUniform().subscribe({
      next: (state) => {
        if (state.scene === 'closet') {
          void this.router.navigateByUrl('/phase1/closet');
          return;
        }
        this.showUniformDenied = state.uniformDenied;
      },
      error: (error) => this.handleForbidden(error),
    });
  }

  protected submitLostBadge(): void {
    if (this.submittingBadge) return;
    this.submittingBadge = true;
    this.changingRoomService.submitLostBadge(this.guardNameInput, this.guardIdInput).subscribe({
      next: (response) => {
        this.submittingBadge = false;
        this.badgeMessage = response.message;
        this.badgeVariant = response.success || response.message === 'Verification checkpoint opened' ? 'success' : 'error';
        this.hasTemporaryBadge = response.temporaryBadgeIssued;
        this.lostBadgeStage = response.stage === 'guard-id' ? 'guard-id' : 'guard-name';
        if (response.busted) {
          this.showLostBadge = false;
          this.showBusted = true;
        }
      },
      error: () => {
        this.submittingBadge = false;
        this.badgeMessage = 'Recovery request denied';
        this.badgeVariant = 'error';
      },
    });
  }

  protected submitUniformClaims(): void {
    if (this.submittingClaims) return;
    this.submittingClaims = true;
    this.changingRoomService.queryUniformClaims(this.claimsFilterField, this.claimsFilterValue).subscribe({
      next: (response) => {
        this.submittingClaims = false;
        this.claimsMessage = response.rows?.length ? `${response.message}\n${JSON.stringify(response.rows, null, 2)}` : response.message;
      },
      error: () => {
        this.submittingClaims = false;
        this.claimsMessage = 'Only guards are allowed to use the search function.';
      },
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
        void this.router.navigateByUrl('/phase1/changing-room');
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
