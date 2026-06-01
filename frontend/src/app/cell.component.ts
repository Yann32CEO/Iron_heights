import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase1Service } from './phase1.service';
import { Phase1CellState } from './phase1.types';

@Component({
  selector: 'app-cell',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, PlayerProfileButtonComponent],
  template: `
    @if (cellState) {
      <main class="hero-shell" aria-label="Iron Heights cell phase">
        <div class="hero-bg hero-bg--cell" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase"></div>

        <section class="phase-layout">
          <app-player-profile-button [alias]="cellState.alias" [role]="cellState.role"></app-player-profile-button>

          <section class="hud-stack" aria-label="Phase 1 status panels">
            <div class="status-hud-card" aria-label="Times caught counter">
              <span class="status-hud-card__label">Times Caught</span>
              <strong>{{ cellState.caughtCount }}</strong>
            </div>
          </section>

          <section class="code-panel code-panel--cell" aria-label="Cell code entry">
            <h1 class="code-panel__title">Cell Lock</h1>
            @if (cellError) {
              <p class="status-banner status-banner--error">{{ cellError }}</p>
            }
            <form class="code-panel__form" [formGroup]="cellForm" (ngSubmit)="openCell()">
              <input class="code-panel__input" type="text" formControlName="cellCode" placeholder="Enter cell code" autocomplete="off" />
              <button class="action-button" type="submit" [disabled]="openingCell">{{ openingCell ? 'Opening...' : 'Open' }}</button>
            </form>
          </section>

          <div class="utility-zone utility-zone--left">
            <button class="action-button action-button--ghost" type="button" (click)="showCode = true">Code</button>
          </div>

          <div class="utility-zone utility-zone--right">
            <button class="action-button action-button--ghost" type="button" (click)="showInfo = true">Info</button>
          </div>
        </section>

        @if (showInfo) {
          <div class="info-modal" role="dialog" aria-modal="true" aria-label="Phase 1 instructions">
            <div class="info-modal__backdrop" (click)="showInfo = false"></div>
            <section class="info-modal__card">
              <div class="info-modal__header">
                <h2>{{ cellState.instructions.title }}</h2>
                <button class="close-button" type="button" (click)="showInfo = false" aria-label="Close instructions">×</button>
              </div>
              <div class="info-modal__body">
                @for (line of cellState.instructions.body; track line) {
                  <p>{{ line }}</p>
                }
              </div>
            </section>
          </div>
        }

        @if (showCode) {
          <div class="info-modal" role="dialog" aria-modal="true" aria-label="Door code details">
            <div class="info-modal__backdrop" (click)="showCode = false"></div>
            <section class="info-modal__card">
              <div class="info-modal__header">
                <h2>Door Code</h2>
                <button class="close-button" type="button" (click)="showCode = false" aria-label="Close code details">×</button>
              </div>
              <div class="info-modal__body">
                <p>
                  An intercepted transfer transmission was recovered from facility traffic, but the relevant section appears to have been truncated. You can retrieve the capture
                  <a href="/api/phase1/transfer-intercept.pcap" download> here</a>.
                </p>
                <section class="crypto-dump" aria-label="Cell lock encrypted payload">
                  <h3 class="crypto-dump__title">Encrypted Payload</h3>
                  <div class="crypto-dump__grid">
                    <div class="crypto-dump__row">
                      <span class="crypto-dump__label">Ciphertext</span>
                      <code class="crypto-dump__value crypto-dump__value--long">{{ cellState.lockCiphertext }}</code>
                    </div>
                  </div>
                </section>
              </div>
            </section>
          </div>
        }

        @if (successFlag) {
          <div class="info-modal info-modal--priority" role="dialog" aria-modal="true" aria-label="Cell opened successfully">
            <div class="info-modal__backdrop"></div>
            <section class="info-modal__card busted-modal">
              <div class="info-modal__header">
                <h2>Cell Opened</h2>
              </div>
              <div class="info-modal__body">
                <p>Nice work. You broke the lock sequence and earned your first flag.</p>
                <p><strong>Flag:</strong> <code>{{ successFlag }}</code></p>
                <button class="action-button busted-modal__button" type="button" (click)="goToCorridor()">Go to Corridor</button>
              </div>
            </section>
          </div>
        }
      </main>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class CellComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly phase1Service = inject(Phase1Service);
  private readonly router = inject(Router);

  protected readonly cellForm = this.fb.nonNullable.group({
    cellCode: ['', [Validators.required]],
  });

  protected cellState: Phase1CellState | null = null;
  protected openingCell = false;
  protected cellError = '';
  protected showInfo = false;
  protected showCode = false;
  protected successFlag = '';

  ngOnInit(): void {
    this.phase1Service.getCellState().subscribe({
      next: (state) => {
        this.cellState = state;
      },
      error: (error) => {
        if (isForbiddenError(error)) {
          void this.router.navigateByUrl('/403');
        }
      },
    });
  }

  protected openCell(): void {
    if (this.cellForm.invalid || this.openingCell) {
      this.cellForm.markAllAsTouched();
      return;
    }

    this.openingCell = true;
    this.cellError = '';

    this.phase1Service.openCell(this.cellForm.getRawValue().cellCode).subscribe({
      next: (response) => {
        if (!response.success) {
          this.cellError = response.error === 'incorrect-code'
            ? 'Incorrect code. Metal groans, the mechanism holds, and the cell stays sealed.'
            : 'Cell unlock failed.';
          this.openingCell = false;
          return;
        }

        this.successFlag = response.flag ?? '';
        this.openingCell = false;
      },
      error: (error) => {
        if (isForbiddenError(error)) {
          void this.router.navigateByUrl('/403');
          return;
        }
        this.cellError = 'Cell unlock failed.';
        this.openingCell = false;
      },
    });
  }

  protected goToCorridor(): void {
    this.successFlag = '';
    void this.router.navigateByUrl('/phase1/corridor');
  }
}
