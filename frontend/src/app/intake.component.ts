import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';

import { SessionService } from './session.service';

@Component({
  selector: 'app-intake',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <main class="hero-shell" aria-label="Iron Heights entrance screen">
      <div class="hero-bg hero-bg--intake" aria-hidden="true"></div>
      <div class="hero-overlay"></div>

      <section class="hero-content">
        <form class="entry-panel" [formGroup]="intakeForm" (ngSubmit)="submit()" autocomplete="off">
          <label class="entry-panel__label" for="alias">Choose your inmate alias</label>
          <div class="entry-panel__row">
            <input id="alias" class="entry-panel__input" type="text" formControlName="alias" maxlength="24" required placeholder="e.g. ghostwire" />
            <button class="action-button" type="submit" [disabled]="submitting">{{ submitting ? 'Entering...' : 'Enter' }}</button>
          </div>
          @if (errorMessage) {
            <p class="entry-panel__error">{{ errorMessage }}</p>
          }
        </form>
      </section>
    </main>
  `,
  styleUrl: './shared-ui.css',
})
export class IntakeComponent {
  private readonly fb = inject(FormBuilder);
  private readonly sessionService = inject(SessionService);
  private readonly router = inject(Router);

  protected readonly intakeForm = this.fb.nonNullable.group({
    alias: ['', [Validators.required, Validators.maxLength(24)]],
  });

  protected submitting = false;
  protected errorMessage = '';

  protected submit(): void {
    if (this.intakeForm.invalid || this.submitting) {
      this.intakeForm.markAllAsTouched();
      return;
    }

    this.submitting = true;
    this.errorMessage = '';

    this.sessionService.createSession(this.intakeForm.getRawValue().alias).subscribe({
      next: (session) => {
        this.submitting = false;
        const target = session.scene === 'corridor' ? '/phase1/corridor' : session.scene === 'yard' ? '/phase1/yard' : '/phase1';
        void this.router.navigateByUrl(target);
      },
      error: () => {
        this.errorMessage = 'Intake failed. Try a different alias.';
        this.submitting = false;
      },
    });
  }
}
