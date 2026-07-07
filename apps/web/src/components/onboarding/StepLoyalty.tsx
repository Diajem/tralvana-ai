"use client";

import { useState } from "react";
import type { TravellerLoyalty } from "@/types/traveller";

interface Props {
  value: TravellerLoyalty;
  onChange: (v: TravellerLoyalty) => void;
}

const inputClass =
  "border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500";

export default function StepLoyalty({ value, onChange }: Props) {
  const [airline, setAirline] = useState({ carrier: "", number: "" });
  const [hotel, setHotel] = useState({ brand: "", number: "" });

  const addAirline = () => {
    if (!airline.carrier || !airline.number) return;
    onChange({
      ...value,
      airline_programs: [...value.airline_programs, { ...airline }],
    });
    setAirline({ carrier: "", number: "" });
  };

  const removeAirline = (i: number) =>
    onChange({
      ...value,
      airline_programs: value.airline_programs.filter((_, j) => j !== i),
    });

  const addHotel = () => {
    if (!hotel.brand || !hotel.number) return;
    onChange({
      ...value,
      hotel_programs: [...value.hotel_programs, { ...hotel }],
    });
    setHotel({ brand: "", number: "" });
  };

  const removeHotel = (i: number) =>
    onChange({
      ...value,
      hotel_programs: value.hotel_programs.filter((_, j) => j !== i),
    });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900">Loyalty programs</h2>
        <p className="text-sm text-gray-500 mt-1">
          Optional. TravelOS uses these to prioritise your preferred carriers.
        </p>
      </div>

      {/* Airlines */}
      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">Airline programs</p>
        <div className="flex gap-2">
          <input
            value={airline.carrier}
            onChange={(e) => setAirline((a) => ({ ...a, carrier: e.target.value }))}
            placeholder="Carrier (e.g. LH)"
            className={`flex-1 ${inputClass}`}
          />
          <input
            value={airline.number}
            onChange={(e) => setAirline((a) => ({ ...a, number: e.target.value }))}
            placeholder="Member number"
            className={`flex-1 ${inputClass}`}
          />
          <button
            onClick={addAirline}
            className="px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          >
            Add
          </button>
        </div>
        {value.airline_programs.map((p, i) => (
          <div
            key={i}
            className="mt-2 flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg"
          >
            <span>{p.carrier} — {p.number}</span>
            <button onClick={() => removeAirline(i)} className="text-red-400 hover:text-red-600 ml-3">
              ×
            </button>
          </div>
        ))}
      </div>

      {/* Hotels */}
      <div>
        <p className="text-sm font-medium text-gray-700 mb-2">Hotel programs</p>
        <div className="flex gap-2">
          <input
            value={hotel.brand}
            onChange={(e) => setHotel((h) => ({ ...h, brand: e.target.value }))}
            placeholder="Brand (e.g. Marriott)"
            className={`flex-1 ${inputClass}`}
          />
          <input
            value={hotel.number}
            onChange={(e) => setHotel((h) => ({ ...h, number: e.target.value }))}
            placeholder="Member number"
            className={`flex-1 ${inputClass}`}
          />
          <button
            onClick={addHotel}
            className="px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
          >
            Add
          </button>
        </div>
        {value.hotel_programs.map((p, i) => (
          <div
            key={i}
            className="mt-2 flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg"
          >
            <span>{p.brand} — {p.number}</span>
            <button onClick={() => removeHotel(i)} className="text-red-400 hover:text-red-600 ml-3">
              ×
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
