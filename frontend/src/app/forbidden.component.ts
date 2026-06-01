import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';

import { SessionService } from './session.service';

@Component({
  selector: 'app-forbidden',
  standalone: true,
  template: `
    <main class="forbidden-shell">
      <section class="forbidden-card">
        <span class="forbidden-code">403</span>
        <h1>Restricted Block</h1>
        <p>Iron Heights is returning you to your last authorized checkpoint.</p>
      </section>
    </main>
  `,
  styles: `
    .forbidden-shell {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 1.5rem;
      background: #120b09;
      color: #f8ead7;
      font-family: Inter, "Segoe UI", Roboto, sans-serif;
    }

    .forbidden-card {
      width: min(100%, 32rem);
      padding: 2rem;
      text-align: center;
      border-radius: 28px;
      border: 1px solid rgba(213, 179, 142, 0.24);
      background: rgba(15, 8, 7, 0.66);
      box-shadow: 0 28px 72px rgba(0, 0, 0, 0.54);
      backdrop-filter: blur(16px);
    }

    .forbidden-code {
      display: inline-block;
      margin-bottom: 0.85rem;
      color: #e6c4a4;
      font-size: 0.76rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }

    h1 {
      margin: 0 0 0.8rem;
      font-size: clamp(2rem, 4vw, 3.6rem);
      line-height: 1.02;
    }

    p {
      margin: 0 0 1.2rem;
      color: rgba(248, 234, 215, 0.82);
      line-height: 1.65;
    }

  `,
})
export class ForbiddenComponent implements OnInit {
  private readonly router = inject(Router);
  private readonly sessionService = inject(SessionService);

  ngOnInit(): void {
    this.sessionService.getProfile().subscribe({
      next: (profile) => void this.router.navigateByUrl(this.routeForScene(profile.scene)),
      error: () => void this.router.navigateByUrl('/intake'),
    });
  }

  private routeForScene(scene: string): string {
    // This map is the frontend half of the backend scene contract; unknown or stale scenes must not leak future routes.
    const routes: Record<string, string> = {
      intake: '/intake',
      cell: '/phase1',
      corridor: '/phase1/corridor',
      yard: '/phase1/yard',
      'changing-room': '/phase1/changing-room',
      closet: '/phase1/closet',
      'phase2/security-hall': '/phase2/security-hall',
      'phase2/artemis': '/phase2/artemis',
      'phase2/kitchen-sector': '/phase2/kitchen-sector',
      'phase2/director-office': '/phase2/director-office',
      'director-office/inside': '/director-office/inside',
      'phase3/director-diary': '/phase3/director-diary',
      'phase3/finale': '/phase3/finale',
    };

    return routes[scene] ?? '/intake';
  }
}
