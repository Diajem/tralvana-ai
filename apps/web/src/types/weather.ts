export type WeatherStatus =
  | "EXCELLENT"
  | "GOOD"
  | "ACCEPTABLE"
  | "CHALLENGING"
  | "NOT_RECOMMENDED";

export interface AlternativeMonth {
  month: number;
  month_name: string;
  weather_status: WeatherStatus;
  weather_suitability_score: number;
}

export interface WeatherAssessment {
  weather_assessment_id: string;
  traveller_id: string | null;
  trip_id: string | null;
  destination: string;
  month_of_travel: number;
  season: string;
  average_temperature: number | null;
  rainfall_level: string;
  humidity_level: string;
  daylight_hours: number | null;
  weather_summary: string;
  weather_suitability_score: number;
  outdoor_activity_score: number;
  photography_score: number;
  family_score: number;
  transport_disruption_risk: string;
  natural_hazard_risk: string;
  health_risk: string;
  personal_suitability: string;
  packing_recommendations: string[];
  safety_summary: string;
  risks: string[];
  assumptions: string[];
  confidence: number;
  weather_status: WeatherStatus;
  alternative_months: AlternativeMonth[];
  recommendation: string;
  explanation: string;
  created_at: string;
}

export interface AnalyseWeatherRequest {
  traveller_id?: string;
  trip_id?: string;
  destination: string;
  month_of_travel?: number;
  goal_type?: string;
}
