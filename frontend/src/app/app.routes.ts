import { Routes } from '@angular/router';

import { CellComponent } from './cell.component';
import { ChangingRoomComponent } from './changing-room.component';
import { ClosetComponent } from './closet.component';
import { CorridorComponent } from './corridor.component';
import { ArtemisComponent } from './artemis.component';
import { DirectorOfficeComponent } from './director-office.component';
import { DirectorDiaryComponent } from './director-diary.component';
import { DirectorOfficeInsideComponent } from './director-office-inside.component';
import { ForbiddenComponent } from './forbidden.component';
import { IntakeComponent } from './intake.component';
import { KitchenSectorComponent } from './kitchen-sector.component';
import { SecurityHallComponent } from './security-hall.component';
import { Phase3FinaleComponent } from './phase3-finale.component';
import { YardComponent } from './yard.component';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'intake' },
  { path: 'intake', component: IntakeComponent },
  { path: 'phase1', component: CellComponent },
  { path: 'phase1/corridor', component: CorridorComponent },
  { path: 'phase1/yard', component: YardComponent },
  { path: 'phase1/changing-room', component: ChangingRoomComponent },
  { path: 'phase1/closet', component: ClosetComponent },
  { path: 'phase2', pathMatch: 'full', redirectTo: 'phase2/security-hall' },
  { path: 'phase2/security-hall', component: SecurityHallComponent },
  { path: 'phase2/artemis', component: ArtemisComponent },
  { path: 'phase2/kitchen-sector', component: KitchenSectorComponent },
  { path: 'phase2/director-office', component: DirectorOfficeComponent },
  // Phase 3 starts from the V1-compatible Director Office path produced by the Phase 2 door handoff.
  { path: 'director-office/inside', component: DirectorOfficeInsideComponent },
  { path: 'phase3/director-diary', component: DirectorDiaryComponent },
  { path: 'phase3/finale', component: Phase3FinaleComponent },
  { path: '403', component: ForbiddenComponent },
  { path: '**', redirectTo: '403' },
];
