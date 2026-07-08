export type GoalType =
  | "RELAXATION"
  | "ADVENTURE"
  | "FOOTBALL_TRAVEL"
  | "FAMILY_TRIP"
  | "BUSINESS_TRAVEL"
  | "FOOD_TOUR"
  | "PHOTOGRAPHY"
  | "PILGRIMAGE"
  | "DIASPORA_TRAVEL"
  | "ROMANTIC_TRIP"
  | "GENERAL_TRAVEL";

export type GoalStatus =
  | "DRAFT"
  | "ACTIVE"
  | "READY_FOR_PLANNING"
  | "PLANNED"
  | "ARCHIVED";

export interface Budget {
  min_usd: number | null;
  max_usd: number | null;
  currency: string;
}

export interface Timeframe {
  earliest: string | null;
  latest: string | null;
  duration_days: number | null;
  flexible: boolean;
}

export interface TravellersCount {
  adults: number;
  children: number;
  infants: number;
}

export interface Flexibility {
  dates: boolean;
  duration: boolean;
  budget: boolean;
}

export interface Goal {
  goal_id: string;
  traveller_id: string;
  title: string;
  goal_type: GoalType;
  priority: number;
  budget: Budget;
  timeframe: Timeframe;
  travellers: TravellersCount;
  interests: string[];
  constraints: string[];
  success_criteria: string[];
  flexibility: Flexibility;
  status: GoalStatus;
  created_at: string;
  updated_at: string;
}

export interface CreateGoalRequest {
  traveller_id: string;
  title: string;
  goal_type: GoalType;
  priority: number;
  budget: Budget;
  timeframe: Timeframe;
  travellers: TravellersCount;
  interests: string[];
  constraints: string[];
  success_criteria: string[];
  flexibility: Flexibility;
}

export interface GoalReasoning {
  goal_summary: string;
  missing_information: string[];
  planning_readiness_score: number;
  recommended_next_actions: string[];
  suitable_agents: string[];
}
