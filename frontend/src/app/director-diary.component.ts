import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase3Service } from './phase3.service';
import { DiaryEntryPayload, DirectorDiaryState, DuplicateDiaryEntryResponse } from './phase3.types';

@Component({
  selector: 'app-director-diary',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Director diary">
        <section class="phase-layout diary-layout">
          <a class="nav-chip" routerLink="/director-office/inside">Back to Office</a>
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>
          <section class="phase2-panel diary-panel">
            <span class="code-panel__eyebrow">Director Halden</span>
            <h1 class="code-panel__title">Director Diary</h1>
            <p class="code-panel__subtitle">Total Entries: {{ state.totalEntries }}</p>

            <div class="diary-entry-card">
              <h2>{{ state.activeSubject }}</h2>
              <p>{{ state.activeContent }}</p>
            </div>

            <div class="diary-grid diary-grid--single">
              <form (ngSubmit)="createEntry()" class="changing-room-form">
                <h3>Create Entry</h3>
                <input class="entry-panel__input" type="text" [(ngModel)]="subject" name="subject" placeholder="Subject" />
                <textarea class="entry-panel__input phase3-jwt-input" [(ngModel)]="content" name="content" placeholder="Content"></textarea>
                <button class="action-button" type="submit" [disabled]="submitting || !subject.trim() || !content.trim()">{{ submitting ? 'Creating...' : 'Create Entry' }}</button>
              </form>
            </div>

            @if (message) { <div class="status-banner" [class.status-banner--success]="saved" [class.status-banner--error]="!saved">{{ message }}</div> }

            @if (state.createdEntries.length > 0) {
              <div class="crypto-dump">
                <h3 class="crypto-dump__title">Recent Entries</h3>
                <div class="crypto-dump__grid">
                  @for (entry of state.createdEntries; track entry.id + '-' + entry.subject) {
                    <div class="crypto-dump__row">
                      <span class="crypto-dump__label">Entry {{ entry.id }}</span>
                      <code class="crypto-dump__value">{{ entry.subject }}</code>
                      <code class="crypto-dump__value crypto-dump__value--long">{{ entry.content }}</code>
                    </div>
                  }
                </div>
              </div>
            }

            @if (leakedEntry) {
              <div class="crypto-dump">
                <h3 class="crypto-dump__title">Archive Conflict</h3>
                <div class="crypto-dump__grid">
                  <div class="crypto-dump__row">
                    <span class="crypto-dump__label">Subject</span>
                    <code class="crypto-dump__value">{{ leakedEntry.subject }}</code>
                  </div>
                  <div class="crypto-dump__row">
                    <span class="crypto-dump__label">Content</span>
                    <code class="crypto-dump__value crypto-dump__value--long">{{ leakedEntry.content }}</code>
                  </div>
                </div>
              </div>
            }
          </section>
        </section>
      </main>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class DirectorDiaryComponent implements OnInit {
  // The 409 duplicate-subject response is intentional gameplay content and must stay visible here.
  private readonly phase3Service = inject(Phase3Service);
  protected readonly router = inject(Router);
  protected state: DirectorDiaryState | null = null;
  protected subject = '';
  protected content = '';
  protected submitting = false;
  protected message = '';
  protected saved = false;
  protected leakedEntry: DiaryEntryPayload | null = null;

  ngOnInit(): void {
    this.phase3Service.getDirectorDiary().subscribe({
      next: (state) => { this.state = state; },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }

  createEntry(): void {
    this.submitting = true;
    this.message = '';
    this.leakedEntry = null;
    this.phase3Service.createDiaryEntry(this.subject, this.content).subscribe({
      next: (result) => {
        this.submitting = false;
        this.saved = result.success;
        this.message = result.message;
        if (result.entry && this.state) this.state = { ...this.state, totalEntries: this.state.totalEntries + 1, createdEntries: [...this.state.createdEntries, result.entry] };
        this.subject = '';
        this.content = '';
      },
      error: (error: HttpErrorResponse) => {
        this.submitting = false;
        if (isForbiddenError(error)) { void this.router.navigateByUrl('/403'); return; }
        const duplicate = error.error as DuplicateDiaryEntryResponse;
        if (error.status === 409 && duplicate?.error === 'duplicate_subject') {
          this.saved = false;
          this.message = duplicate.message;
          this.leakedEntry = duplicate.existingEntry;
          return;
        }
        this.saved = false;
        this.message = 'Diary service failed to store the entry.';
      },
    });
  }
}
