"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import StepIdentity from "@/components/onboarding/StepIdentity";
import StepTravelStyle from "@/components/onboarding/StepTravelStyle";
import StepPreferences from "@/components/onboarding/StepPreferences";
import StepLoyalty from "@/components/onboarding/StepLoyalty";
import { createProfile } from "@/lib/api";
import type {
  TravellerIdentity,
  TravellerPreferences,
  TravellerLoyalty,
} from "@/types/traveller";

const STEPS = ["Identity", "Travel Style", "Comfort", "Loyalty"];

const defaultIdentity: TravellerIdentity = {
  name: "",
  email: "",
  locale: "en",
  timezone: "UTC",
};

const defaultPreferences: TravellerPreferences = {
  home_airport: "",
  preferred_currency: "USD",
  preferred_language: "en",
  budget_style: "balanced",
  travel_interests: [],
  seat: "no_preference",
  cabin_class: "economy",
  meal: "standard",
  accommodation_type: "hotel",
  hotel_preferences: [],
  accessibility_needs: [],
};

const defaultLoyalty: TravellerLoyalty = {
  airline_programs: [],
  hotel_programs: [],
};

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [identity, setIdentity] = useState<TravellerIdentity>(defaultIdentity);
  const [preferences, setPreferences] =
    useState<TravellerPreferences>(defaultPreferences);
  const [loyalty, setLoyalty] = useState<TravellerLoyalty>(defaultLoyalty);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const profile = await createProfile({ identity, preferences, loyalty });
      router.push(`/profile/${profile.id}`);
    } catch {
      setError(
        "Failed to create profile. Make sure the API is running on port 8000."
      );
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-sm p-8">
        {/* Header */}
        <div className="mb-8">
          <p className="text-sm font-medium text-indigo-600">TravelOS</p>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">
            Create your Traveller Profile
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Step {step + 1} of {STEPS.length}
          </p>
        </div>

        {/* Step indicator */}
        <div className="flex items-center mb-8 gap-1">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center flex-1 last:flex-none">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 transition-colors ${
                  i < step
                    ? "bg-indigo-600 text-white"
                    : i === step
                    ? "bg-indigo-600 text-white ring-4 ring-indigo-100"
                    : "bg-gray-100 text-gray-400"
                }`}
              >
                {i < step ? "✓" : i + 1}
              </div>
              <span
                className={`ml-1.5 text-xs hidden sm:inline ${
                  i === step
                    ? "text-gray-900 font-medium"
                    : "text-gray-400"
                }`}
              >
                {label}
              </span>
              {i < STEPS.length - 1 && (
                <div className="flex-1 mx-2 h-px bg-gray-200" />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        {step === 0 && (
          <StepIdentity value={identity} onChange={setIdentity} />
        )}
        {step === 1 && (
          <StepTravelStyle value={preferences} onChange={setPreferences} />
        )}
        {step === 2 && (
          <StepPreferences value={preferences} onChange={setPreferences} />
        )}
        {step === 3 && (
          <StepLoyalty value={loyalty} onChange={setLoyalty} />
        )}

        {error && (
          <p className="mt-4 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
            {error}
          </p>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-100">
          <button
            onClick={() => setStep((s) => s - 1)}
            disabled={step === 0}
            className="px-4 py-2 text-sm text-gray-500 disabled:opacity-30"
          >
            Back
          </button>

          {step < STEPS.length - 1 ? (
            <button
              onClick={() => setStep((s) => s + 1)}
              className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 font-medium"
            >
              Continue
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={submitting}
              className="px-6 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 font-medium disabled:opacity-50"
            >
              {submitting ? "Creating profile..." : "Create profile"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
