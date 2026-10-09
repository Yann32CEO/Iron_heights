export interface ExposurePayload {
  state: string;
  message: string;
}

export interface MealReviewPayload {
  authorRole: string;
  authorName: string;
  text: string;
  // Seeded catalog reviews carry no rating; only player submissions do.
  rating?: string | null;
}

export interface MealPayload {
  id: string;
  name: string;
  shift: 'regular' | 'late-night';
  orderingAllowed: boolean;
  favorite: boolean;
  reviews: MealReviewPayload[];
}

export interface MealCatalogPayload {
  regular: MealPayload[];
  lateNight: MealPayload[];
}

export interface Phase2State {
  alias: string;
  role: string;
  phase: string;
  scene: string;
  caughtCount: number;
  exposure: ExposurePayload;
  promptCount: number;
  reviewPoisoned: boolean;
  latestAiReply: string;
  artemisGreeting: string;
  instructions?: { title: string; body: string[] } | null;
  mealsCatalog?: MealCatalogPayload | null;
  selectedMeal?: MealPayload | null;
  directorOfficeAccessGranted: boolean;
  captured: boolean;
}

export type SecurityHallState = Phase2State;

export interface ArtemisChatResponse {
  reply: string;
  exposure: ExposurePayload;
  directProbeSeen: boolean;
  codeLeaked: boolean;
  promptCount: number;
  captured: boolean;
  attackDetected: boolean;
  busted: boolean;
  bustedTitle: string;
  bustedMessage: string;
  redirectTo?: string | null;
}

export interface KitchenOrderResponse {
  message: string;
  selectedMeal?: MealPayload | null;
  exposure: ExposurePayload;
  captured: boolean;
  attackDetected: boolean;
  busted: boolean;
  bustedTitle: string;
  bustedMessage: string;
  redirectTo?: string | null;
}

export interface KitchenReviewResponse {
  message: string;
  selectedMeal?: MealPayload | null;
  exposure: ExposurePayload;
  reviewStored: boolean;
  reviewPoisoned: boolean;
  impersonationUsed: boolean;
  duplicateReview: boolean;
  invalidReview: boolean;
  captured: boolean;
  statusPopup?: { title: string; state: string; message: string } | null;
  attackDetected: boolean;
  busted: boolean;
  bustedTitle: string;
  bustedMessage: string;
  redirectTo?: string | null;
}

export interface DirectorDoorResponse {
  success: boolean;
  message: string;
  exposure: ExposurePayload;
  alertFlag: string;
  captured: boolean;
  attackDetected: boolean;
  busted: boolean;
  bustedTitle: string;
  bustedMessage: string;
  redirectTo?: string | null;
}

export interface ResetCheckpointResponse {
  success: boolean;
  redirectTo: string;
  caughtCount: number;
  exposure: ExposurePayload;
}

