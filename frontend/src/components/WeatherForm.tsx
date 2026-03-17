"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { weatherClient } from "@/lib/api/weatherClient";
import { useWeatherStore } from "@/store/weatherStore";
import { notify } from "@/components/Notification";
import {
  cityFormSchema,
  coordsFormSchema,
  CityFormValues,
  CoordsFormValues,
} from "@/lib/validations/weather.schema";
import { WeatherResponse } from "@/types/weather";

type Mode = "city" | "coords";

export function WeatherForm() {
  const [mode, setMode] = useState<Mode>("city");
  const router = useRouter();
  const { setWeatherData, setLoading, setError } = useWeatherStore();

  const cityForm = useForm<CityFormValues>({
    resolver: zodResolver(cityFormSchema),
    defaultValues: { mode: "city", city: "", country: "" },
  });

  const coordsForm = useForm<CoordsFormValues>({
    resolver: zodResolver(coordsFormSchema),
    defaultValues: { mode: "coords", latitude: 0, longitude: 0 },
  });

  const handleSubmit = async (fetchFn: () => Promise<WeatherResponse>) => {
    setLoading(true);
    try {
      const weather = await fetchFn();
      setWeatherData(weather);
      notify.success("Weather fetched successfully!");
      router.push("/result");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to fetch weather";
      setError(message);
      notify.error(message);
    } finally {
      setLoading(false);
    }
  };

  const handleCitySubmit = (data: CityFormValues) =>
    handleSubmit(() => weatherClient.fetchByCity(data.city, data.country));

  const handleCoordsSubmit = (data: CoordsFormValues) =>
    handleSubmit(() => weatherClient.fetchByCoords(data.latitude, data.longitude));

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="flex mb-6 rounded-lg overflow-hidden border border-gray-200">
        <button
          onClick={() => setMode("city")}
          className={`flex-1 py-2 text-sm font-medium transition-colors ${
            mode === "city" ? "bg-blue-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
          }`}
        >
          City / Country
        </button>
        <button
          onClick={() => setMode("coords")}
          className={`flex-1 py-2 text-sm font-medium transition-colors ${
            mode === "coords" ? "bg-blue-600 text-white" : "bg-white text-gray-600 hover:bg-gray-50"
          }`}
        >
          Coordinates
        </button>
      </div>

      {mode === "city" ? (
        <form onSubmit={cityForm.handleSubmit(handleCitySubmit)} className="space-y-4">
          <input type="hidden" {...cityForm.register("mode")} />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
            <input
              {...cityForm.register("city")}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. London"
            />
            {cityForm.formState.errors.city && (
              <p className="mt-1 text-sm text-red-600">{cityForm.formState.errors.city.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Country Code</label>
            <input
              {...cityForm.register("country")}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g. GB"
              maxLength={2}
            />
            {cityForm.formState.errors.country && (
              <p className="mt-1 text-sm text-red-600">{cityForm.formState.errors.country.message}</p>
            )}
          </div>
          <button
            type="submit"
            disabled={cityForm.formState.isSubmitting}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {cityForm.formState.isSubmitting ? "Fetching..." : "Get Weather"}
          </button>
        </form>
      ) : (
        <form onSubmit={coordsForm.handleSubmit(handleCoordsSubmit)} className="space-y-4">
          <input type="hidden" {...coordsForm.register("mode")} />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Latitude</label>
            <input
              type="number"
              step="any"
              {...coordsForm.register("latitude")}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="-90 to 90"
            />
            {coordsForm.formState.errors.latitude && (
              <p className="mt-1 text-sm text-red-600">{coordsForm.formState.errors.latitude.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Longitude</label>
            <input
              type="number"
              step="any"
              {...coordsForm.register("longitude")}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="-180 to 180"
            />
            {coordsForm.formState.errors.longitude && (
              <p className="mt-1 text-sm text-red-600">{coordsForm.formState.errors.longitude.message}</p>
            )}
          </div>
          <button
            type="submit"
            disabled={coordsForm.formState.isSubmitting}
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {coordsForm.formState.isSubmitting ? "Fetching..." : "Get Weather"}
          </button>
        </form>
      )}
    </div>
  );
}
