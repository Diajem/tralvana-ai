export type VisaStatus =
  | "VISA_NOT_REQUIRED"
  | "VISA_REQUIRED"
  | "ETA_REQUIRED"
  | "EVISA_AVAILABLE"
  | "CHECK_MANUALLY"
  | "ENTRY_RESTRICTED";

export type TravelPurpose =
  | "TOURISM"
  | "BUSINESS"
  | "TRANSIT"
  | "STUDY"
  | "WORK"
  | "FAMILY_VISIT"
  | "OTHER";

export interface VisaAssessment {
  visa_assessment_id: string;
  traveller_id: string | null;
  trip_id: string | null;
  nationality: string;
  passport_country: string;
  destination_country: string;
  transit_countries: string[];
  travel_purpose: string;
  intended_length_of_stay: number;
  passport_expiry_date: string | null;
  passport_validity_months: number | null;
  visa_status: VisaStatus;
  visa_required: boolean;
  visa_type: string;
  entry_requirements: string[];
  supporting_documents: string[];
  vaccination_requirements: string[];
  travel_authorisation_required: boolean;
  processing_time: string;
  confidence: number;
  risks: string[];
  assumptions: string[];
  recommendation: string;
  explanation: string;
  created_at: string;
}

export interface CheckVisaRequest {
  traveller_id?: string;
  trip_id?: string;
  nationality?: string;
  passport_country: string;
  destination_country: string;
  transit_countries?: string[];
  travel_purpose?: string;
  intended_length_of_stay?: number;
  passport_expiry_date?: string;
}
