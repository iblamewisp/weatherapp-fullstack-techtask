"use client";
import { useCallback, useEffect, useState } from "react";
import { WeatherForm } from "@/components/WeatherForm";
import { CityCard } from "@/components/CityCard";
import { EditWeatherModal } from "@/components/EditWeatherModal";
import { useWeatherStore } from "@/store/weatherStore";
import { weatherClient } from "@/lib/api/weatherClient";
import { WeatherResponse } from "@/types/weather";

export default function Home() {
  const { recentSearches, updateRecentSearch } = useWeatherStore();
  const [popular, setPopular] = useState<WeatherResponse[]>([]);
  const [popularLoading, setPopularLoading] = useState(true);
  const [popularError, setPopularError] = useState(false);
  const [editing, setEditing] = useState<WeatherResponse | null>(null);

  useEffect(() => {
    weatherClient
      .getPopular()
      .then(setPopular)
      .catch(() => setPopularError(true))
      .finally(() => setPopularLoading(false));
  }, []);

  const handleSave = useCallback((updated: WeatherResponse) => {
    setPopular((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    updateRecentSearch(updated);
    setEditing(null);
  }, [updateRecentSearch]);

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-800 mb-2">Weather App</h1>
        <p className="text-center text-gray-500 mb-8">Search by city or coordinates</p>

        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <WeatherForm />
        </div>

        {recentSearches.length > 0 && (
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-gray-700 mb-3">Recent searches</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {recentSearches.map((city) => (
                <CityCard
                  key={`${city.city}-${city.country}`}
                  weather={city}
                  onEdit={setEditing}
                />
              ))}
            </div>
          </section>
        )}

        <section>
          <h2 className="text-lg font-semibold text-gray-700 mb-3">Popular cities</h2>
          {popularLoading ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-28 rounded-xl bg-gray-200 animate-pulse" />
              ))}
            </div>
          ) : popularError ? (
            <p className="text-red-400 text-sm">Could not load popular cities. The backend may be starting up.</p>
          ) : popular.length === 0 ? (
            <p className="text-gray-400 text-sm">No data yet — the backend is warming up.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {popular.map((city) => (
                <CityCard
                  key={`${city.city}-${city.country}`}
                  weather={city}
                  onEdit={setEditing}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      {editing && (
        <EditWeatherModal
          weather={editing}
          onSave={handleSave}
          onClose={() => setEditing(null)}
        />
      )}
    </main>
  );
}
