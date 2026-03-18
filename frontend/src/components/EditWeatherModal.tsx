"use client";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { WeatherResponse } from "@/types/weather";
import { editWeatherSchema, EditWeatherValues } from "@/lib/validations/weather.schema";
import { weatherClient } from "@/lib/api/weatherClient";
import { notify } from "@/components/Notification";

interface Props {
  weather: WeatherResponse;
  onSave: (updated: WeatherResponse) => void;
  onClose: () => void;
}

interface Field {
  key: keyof EditWeatherValues;
  label: string;
  unit: string;
  step: string;
}

const FIELDS: Field[] = [
  { key: "temperature", label: "Temperature", unit: "°C", step: "0.1" },
  { key: "feels_like", label: "Feels like", unit: "°C", step: "0.1" },
  { key: "humidity", label: "Humidity", unit: "%", step: "1" },
  { key: "pressure", label: "Pressure", unit: "hPa", step: "1" },
  { key: "wind_speed", label: "Wind speed", unit: "m/s", step: "0.1" },
];

export function EditWeatherModal({ weather, onSave, onClose }: Props) {
  const overlayRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EditWeatherValues>({
    resolver: zodResolver(editWeatherSchema),
    defaultValues: {
      temperature: weather.temperature,
      feels_like: weather.feels_like,
      humidity: weather.humidity,
      pressure: weather.pressure,
      wind_speed: weather.wind_speed,
      weather_description: weather.weather_description ?? "",
    },
  });

  // Close on Escape key
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const onSubmit = async (values: EditWeatherValues) => {
    try {
      const updated = await weatherClient.updateById(weather.id, values);
      notify.success("Weather updated");
      onSave(updated);
    } catch (err) {
      notify.error(err instanceof Error ? err.message : "Failed to update");
    }
  };

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => e.target === overlayRef.current && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-modal-title"
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 mx-4"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 id="edit-modal-title" className="text-lg font-semibold text-gray-800">
            Edit — {weather.city}, {weather.country}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none"
            aria-label="Close edit dialog"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          {FIELDS.map(({ key, label, unit, step }) => (
            <div key={key}>
              <label htmlFor={`edit-${key}`} className="block text-sm font-medium text-gray-700 mb-1">
                {label} <span className="text-gray-400 font-normal">({unit})</span>
              </label>
              <input
                id={`edit-${key}`}
                type="number"
                step={step}
                {...register(key)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors[key] && (
                <p className="mt-1 text-xs text-red-600">{errors[key]?.message}</p>
              )}
            </div>
          ))}

          <div>
            <label htmlFor="edit-weather_description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <input
              id="edit-weather_description"
              type="text"
              {...register("weather_description")}
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.weather_description && (
              <p className="mt-1 text-xs text-red-600">
                {errors.weather_description.message}
              </p>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-2 px-4 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
