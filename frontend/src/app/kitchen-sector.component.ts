import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { isForbiddenError } from './http-error.util';
import { PlayerProfileButtonComponent } from './player-profile-button.component';
import { Phase2Service } from './phase2.service';
import { ExposurePayload, MealPayload, Phase2State } from './phase2.types';

@Component({
  selector: 'app-kitchen-sector',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, PlayerProfileButtonComponent],
  template: `
    @if (state) {
      <main class="hero-shell" aria-label="Kitchen sector">
        <div class="hero-bg hero-bg--kitchen-sector" aria-hidden="true"></div>
        <div class="hero-overlay hero-overlay--phase hero-overlay--phase2"></div>
        <section class="phase-layout phase2-layout">
          <app-player-profile-button [alias]="state.alias" [role]="state.role"></app-player-profile-button>
          <section class="hud-stack">
            <button class="status-hud-card status-hud-card--compact status-hud-card--button" type="button" (click)="openStatusPopup(exposure)"><span class="status-hud-card__label">Operational Status</span><strong>{{ exposure.state }}</strong><small class="phase2-status-copy">{{ exposure.message }}</small></button>
            <div class="status-hud-card status-hud-card--compact"><span class="status-hud-card__label">Times Caught</span><strong>{{ state.caughtCount }}</strong></div>
          </section>

          <section class="phase2-kitchen-grid phase2-kitchen-grid--wide">
            <section class="phase2-panel phase2-panel--kitchen-actions">
              <span class="code-panel__eyebrow">Kitchen Sector</span>
              <h1 class="code-panel__title">Meal Distribution & Service Feedback</h1>
              <p class="code-panel__subtitle">Internal meal records can be viewed here. Select a food item, inspect the reviews, then decide whether to place an order or leave feedback.</p>
              <button class="action-button" type="button" (click)="showMealPicker = !showMealPicker">{{ showMealPicker ? 'Hide Food List' : 'Food List' }}</button>
              @if (showMealPicker) {
                <div class="status-banner status-banner--stacked">
                  <select class="code-panel__input claims-form__select" [(ngModel)]="orderedMealId"><option value="">Select a meal</option>@for (meal of allMeals; track meal.id) { <option [value]="meal.id">{{ meal.name }}</option> }</select>
                  <button class="action-button" type="button" (click)="orderMeal()" [disabled]="!orderedMealId || ordering">{{ ordering ? 'Ordering...' : 'Order' }}</button>
                </div>
              }
              @if (orderResponse) { <div class="status-banner">{{ orderResponse }}</div> }
            </section>

            <section class="phase2-panel phase2-panel--review-browser">
              <span class="code-panel__eyebrow">Reviews</span>
              <div class="changing-room-form">
                <select class="code-panel__input claims-form__select" [(ngModel)]="reviewsMealId"><option value="">Select a meal</option>@for (meal of allMeals; track meal.id) { <option [value]="meal.id">{{ meal.name }}</option> }</select>
                <button class="action-button" type="button" (click)="seeReviews()" [disabled]="!reviewsMealId">See Reviews</button>
              </div>
              @if (reviewLookupMeal) {
                <div class="status-banner status-banner--stacked phase2-review-box">
                  <strong>{{ reviewLookupMeal.name }}</strong><span>Type: {{ reviewLookupMeal.shift }}</span><strong>Reviews:</strong>
                  @for (review of reviewLookupMeal.reviews; track review.authorName + review.text) { <span>* {{ review.authorName }}: {{ review.text }}</span> }
                </div>
              } @else { <div class="status-banner">No meal selected for review lookup.</div> }
            </section>

            <section class="phase2-panel phase2-panel--review-form">
              <span class="code-panel__eyebrow">Leave a Review</span>
              <form class="changing-room-form" (ngSubmit)="submitReview()">
                <select class="code-panel__input claims-form__select" [(ngModel)]="reviewForm.mealId" name="mealId"><option value="">Select a meal</option>@for (meal of allMeals; track meal.id) { <option [value]="meal.id">{{ meal.name }}</option> }</select>
                <select class="code-panel__input claims-form__select" [(ngModel)]="reviewForm.rating" name="rating"><option value="1">1 / 5</option><option value="2">2 / 5</option><option value="3">3 / 5</option><option value="4">4 / 5</option><option value="5">5 / 5</option></select>
                <input class="code-panel__input" type="text" [(ngModel)]="reviewForm.reviewerName" name="reviewerName" placeholder="Reviewer name" />
                <textarea class="code-panel__input phase2-textarea" [(ngModel)]="reviewForm.text" name="text" placeholder="Describe the meal, service, or delivery."></textarea>
                <button class="action-button" type="submit" [disabled]="submittingReview || !reviewForm.mealId">{{ submittingReview ? 'Submitting...' : 'Submit Review' }}</button>
              </form>
              @if (reviewResponse) { <div class="status-banner" [class.status-banner--success]="reviewPoisoned">{{ reviewResponse }}</div> }
            </section>
          </section>

          <nav class="phase2-nav phase2-nav--horizontal"><a class="action-button phase2-nav__button" routerLink="/phase2/security-hall">Security Hall</a><a class="action-button phase2-nav__button" routerLink="/phase2/artemis">ARTEMIS</a><a class="action-button phase2-nav__button" routerLink="/phase2/kitchen-sector">Kitchen Sector</a><a class="action-button phase2-nav__button" routerLink="/phase2/director-office">Director's Office</a></nav>
        </section>
        <ng-container *ngTemplateOutlet="modals"></ng-container>
      </main>
    }
    <ng-template #modals>
      @if (statusPopup) { <div class="info-modal"><div class="info-modal__backdrop" (click)="statusPopup = null"></div><section class="info-modal__card status-popup-modal"><div class="info-modal__header"><h2>Operational Status Update</h2><button class="close-button" type="button" (click)="statusPopup = null">×</button></div><div class="info-modal__body"><p><strong>Current State:</strong> {{ statusPopup.state }}</p><p>{{ statusPopup.message }}</p></div></section></div> }
      @if (bustedMessage) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Busted</h2></div><div class="info-modal__body"><p>{{ bustedMessage }}</p><button class="action-button busted-modal__button" type="button" (click)="router.navigateByUrl('/phase1')">Back to Cell</button></div></section></div> }
      @if (captured) { <div class="info-modal info-modal--priority"><div class="info-modal__backdrop"></div><section class="info-modal__card busted-modal"><div class="info-modal__header"><h2>Detainment Initiated</h2></div><div class="info-modal__body"><p>Your recent activity was flagged as inconsistent with assigned staff behavior.</p><button class="action-button busted-modal__button" type="button" (click)="resetCheckpoint()">Return to Checkpoint</button></div></section></div> }
    </ng-template>
  `,
  styleUrl: './shared-ui.css',
})
export class KitchenSectorComponent implements OnInit {
  protected readonly router = inject(Router);
  private readonly phase2Service = inject(Phase2Service);
  protected state: Phase2State | null = null;
  protected exposure: ExposurePayload = { state: 'Nominal', message: '' };
  protected allMeals: MealPayload[] = [];
  protected orderedMealId = '';
  protected reviewsMealId = '';
  protected reviewLookupMeal: MealPayload | null = null;
  protected reviewForm = { mealId: '', rating: '3', reviewerName: '', text: '' };
  protected showMealPicker = false;
  protected ordering = false;
  protected submittingReview = false;
  protected orderResponse = '';
  protected reviewResponse = '';
  protected reviewPoisoned = false;
  protected captured = false;
  protected bustedMessage = '';
  protected statusPopup: ExposurePayload | null = null;

  ngOnInit(): void {
    this.phase2Service.getKitchenSector().subscribe({
      next: (state) => {
        this.state = state; this.exposure = state.exposure;
        this.allMeals = [...(state.mealsCatalog?.regular || []), ...(state.mealsCatalog?.lateNight || [])];
        this.reviewLookupMeal = state.selectedMeal || null;
        this.orderedMealId = state.selectedMeal?.id || '';
        this.reviewsMealId = state.selectedMeal?.id || '';
        this.reviewForm.mealId = state.selectedMeal?.id || '';
        this.reviewForm.reviewerName = state.alias;
        this.reviewPoisoned = state.reviewPoisoned;
      },
      error: (error) => { if (isForbiddenError(error)) void this.router.navigateByUrl('/403'); },
    });
  }

  seeReviews(): void { this.reviewLookupMeal = this.allMeals.find((meal) => meal.id === this.reviewsMealId) || null; }
  openStatusPopup(exposure: ExposurePayload): void { this.statusPopup = exposure; }
  resetCheckpoint(): void { this.phase2Service.resetCheckpoint().subscribe(() => void this.router.navigateByUrl('/phase2/security-hall')); }

  orderMeal(): void {
    this.ordering = true;
    this.phase2Service.orderMeal(this.orderedMealId).subscribe({
      next: (result) => { this.ordering = false; this.handleCommon(result); this.orderResponse = result.message; },
      error: () => { this.ordering = false; this.orderResponse = 'Meal request could not be queued.'; },
    });
  }

  submitReview(): void {
    this.submittingReview = true;
    this.phase2Service.submitReview(this.reviewForm).subscribe({
      next: (result) => {
        this.submittingReview = false; this.handleCommon(result); this.reviewResponse = result.message; this.reviewPoisoned = result.reviewPoisoned;
        if (result.selectedMeal) { this.reviewLookupMeal = result.selectedMeal; this.reviewsMealId = result.selectedMeal.id; }
        if (result.statusPopup) this.statusPopup = { state: result.statusPopup.state, message: result.statusPopup.message };
      },
      error: () => { this.submittingReview = false; this.reviewResponse = 'Kitchen review rejected the report.'; },
    });
  }

  private handleCommon(result: { exposure: ExposurePayload; busted?: boolean; bustedMessage?: string; captured?: boolean; selectedMeal?: MealPayload | null }): void {
    if (result.busted) { this.bustedMessage = result.bustedMessage || 'Security staff are returning you to the cell.'; return; }
    if (result.captured) { this.captured = true; return; }
    const changed = result.exposure.state !== this.exposure.state || result.exposure.message !== this.exposure.message;
    this.exposure = result.exposure;
    if (result.selectedMeal) {
      const index = this.allMeals.findIndex((meal) => meal.id === result.selectedMeal?.id);
      if (index >= 0) this.allMeals[index] = result.selectedMeal;
    }
    if (changed) this.statusPopup = result.exposure;
  }
}
