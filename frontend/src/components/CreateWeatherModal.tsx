"use client";
import { useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createWeatherSchema, CreateWeatherValues } from "@/lib/validations/weather.schema";
import { weatherClient } from "@/lib/api/weatherClient";
import { notify } from "@/components/Notification";
import { WeatherResponse } from "@/types/weather";

interface Props {
  onSave: (created: WeatherResponse) => void;
  onClose: () => void;
}

interface TextField { key: keyof CreateWeatherValues; label: string; required?: boolean }
interface NumField { key: keyof CreateWeatherValues; label: string; unit: string; step: string }

const TEXT_FIELDS: TextField[] = [
  { key: "city", label: "City", required: true },
  { key: "country", label: "Country code (e.g. GB)", required: true },
];

const NUM_FIELDS: NumField[] = [
  { key: "temperature", label: "Temperature", unit: "°C", step: "0.1" },
  { key: "feels_like", label: "Feels like", unit: "°C", step: "0.1" },
  { key: "humidity", label: "Humidity", unit: "%", step: "1" },
  { key: "pressure", label: "Pressure", unit: "hPa", step: "1" },
  { key: "wind_speed", label: "Wind speed", unit: "m/s", step: "0.1" },
];

export function CreateWeatherModal({ onSave, onClose }: Props) {
  const overlayRef = useRef<HTMLDivElement>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateWeatherValues>({
    resolver: zodResolver(createWeatherSchema),
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const onSubmit = async (values: CreateWeatherValues) => {
    try {
      const created = await weatherClient.createRecord(values);
      const populated = await weatherClient.fetchByCity(created.city, created.country);
      notify.success(`Record created for ${populated.city}, ${populated.country}`);
      onSave(populated);
    } catch (err) {
      notify.error(err instanceof Error ? err.message : "Failed to create record");
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
        aria-labelledby="create-modal-title"
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 mx-4 max-h-[90vh] overflow-y-auto"
      >
        <div className="flex items-center justify-between mb-5">
          <h2 id="create-modal-title" className="text-lg font-semibold text-gray-800">
            Add weather record
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none"
            aria-label="Close create dialog"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
          {TEXT_FIELDS.map(({ key, label, required }) => (
            <div key={key}>
              <label htmlFor={`create-${key}`} className="block text-sm font-medium text-gray-700 mb-1">
                {label} {required && <span className="text-red-500">*</span>}
              </label>
              <input
                id={`create-${key}`}
                type="text"
                {...register(key)}
                maxLength={key === "country" ? 2 : 100}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              {errors[key] && (
                <p className="mt-1 text-xs text-red-600">{errors[key]?.message}</p>
              )}
            </div>
          ))}

          <p className="text-xs text-gray-400 pt-1">Optional fields — leave blank to fill later</p>

          {NUM_FIELDS.map(({ key, label, unit, step }) => (
            <div key={key}>
              <label htmlFor={`create-${key}`} className="block text-sm font-medium text-gray-700 mb-1">
                {label} <span className="text-gray-400 font-normal">({unit})</span>
              </label>
              <input
                id={`create-${key}`}
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
            <label htmlFor="create-weather_description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <input
              id="create-weather_description"
              type="text"
              {...register("weather_description")}
              maxLength={100}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
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
              {isSubmitting ? "Creating..." : "Create"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
