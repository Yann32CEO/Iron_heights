import { CommonModule } from '@angular/common';
import { Component, Input, inject } from '@angular/core';

import { SessionService } from './session.service';
import { SessionProfile } from './session.types';

@Component({
  selector: 'app-player-profile-button',
  standalone: true,
  imports: [CommonModule],
  template: `
    <button class="identity-chip identity-chip--phase identity-chip--button" type="button" (click)="openProfile()" aria-label="Open player profile">
      <span class="identity-chip__label">Alias</span><strong>{{ alias }}</strong>
      <span class="identity-chip__divider"></span>
      <span class="identity-chip__label">Status</span><strong>{{ role }}</strong>
    </button>

    @if (profileOpen) {
      <div class="info-modal" role="dialog" aria-modal="true" aria-label="Player profile">
        <div class="info-modal__backdrop" (click)="profileOpen = false"></div>
        <section class="info-modal__card status-popup-modal">
          <div class="info-modal__header">
            <h2>Player Profile</h2>
            <button class="close-button" type="button" (click)="profileOpen = false" aria-label="Close player profile">×</button>
          </div>
          <div class="info-modal__body profile-modal__body">
            <p><strong>Alias:</strong> {{ profile?.alias || alias }}</p>
            <p><strong>Status:</strong> {{ profile?.role || role }}</p>
            <section class="profile-flags" aria-label="Captured flags">
              <h3 class="crypto-dump__title">Captured Flags</h3>
              @if (loadingProfile) {
                <p class="profile-flags__empty">Loading...</p>
              } @else if (profileError) {
                <p class="profile-flags__empty">{{ profileError }}</p>
              } @else if ((profile?.flags?.length || 0) > 0) {
                <ul class="profile-flags__list">
                  @for (flag of profile?.flags || []; track flag) {
                    <li><code>{{ flag }}</code></li>
                  }
                </ul>
              } @else {
                <p class="profile-flags__empty">No flags captured yet.</p>
              }
            </section>
          </div>
        </section>
      </div>
    }
  `,
  styleUrl: './shared-ui.css',
})
export class PlayerProfileButtonComponent {
  private readonly sessionService = inject(SessionService);

  @Input({ required: true }) alias = '';
  @Input({ required: true }) role = '';

  protected profileOpen = false;
  protected loadingProfile = false;
  protected profileError = '';
  protected profile: SessionProfile | null = null;

  protected openProfile(): void {
    this.profileOpen = true;
    this.loadingProfile = true;
    this.profileError = '';
    // Fetch on open so the shared chip always reflects flags awarded by the latest backend action.
    this.sessionService.getProfile().subscribe({
      next: (profile) => {
        this.profile = profile;
        this.loadingProfile = false;
      },
      error: () => {
        this.profileError = 'Profile unavailable.';
        this.loadingProfile = false;
      },
    });
  }
}
