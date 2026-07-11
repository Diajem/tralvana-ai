export interface SourceModule {
  module: string;
  status: string;
}

export interface RecommendationDriver {
  module: string;
  driver: string;
}

export interface AlternativeConsidered {
  module: string;
  alternative: string;
  why_not_chosen: string;
}

export interface Explanation {
  summary: string;
  recommendation_drivers: RecommendationDriver[];
  tradeoffs: string[];
  assumptions: string[];
  risks: string[];
  missing_information: string[];
  confidence: number;
  confidence_explanation: string;
  alternatives_considered: AlternativeConsidered[];
  what_would_change_the_result: string[];
  source_modules: SourceModule[];
}

export interface ModuleResultInput {
  agent_name: string;
  status?: string;
  confidence?: number;
  data?: Record<string, unknown>;
  assumptions?: string[];
  missing_information?: string[];
  risks?: string[];
  recommendations?: string[];
  next_actions?: string[];
}

export interface ExplainRequest {
  conversation_id?: string;
  trip_id?: string;
  module_results?: ModuleResultInput[];
  question?: string;
}
