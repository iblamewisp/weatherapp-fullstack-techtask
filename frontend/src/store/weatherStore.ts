import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { WeatherResponse } from "@/types/weather";

const MAX_RECENT = 5;

interface WeatherStore {
  weatherData: WeatherResponse | null;
  recentSearches: WeatherResponse[];
  isLoading: boolean;
  error: string | null;
  setWeatherData: (data: WeatherResponse) => void;
  addRecentSearch: (data: WeatherResponse) => void;
  updateRecentSearch: (updated: WeatherResponse) => void;
  removeRecentSearch: (id: string) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
}

export const useWeatherStore = create<WeatherStore>()(
  persist(
    (set) => ({
      weatherData: null,
      recentSearches: [],
      isLoading: false,
      error: null,
      setWeatherData: (data) => set({ weatherData: data, error: null }),
      // Deduplicates by city+country, keeps most recent at front, caps at MAX_RECENT.
      addRecentSearch: (data) =>
        set((state) => {
          const filtered = state.recentSearches.filter(
            (r) => !(r.city === data.city && r.country === data.country)
          );
          return { recentSearches: [data, ...filtered].slice(0, MAX_RECENT) };
        }),
      updateRecentSearch: (updated) =>
        set((state) => ({
          recentSearches: state.recentSearches.map((r) =>
            r.id === updated.id ? updated : r
          ),
        })),
      removeRecentSearch: (id) =>
        set((state) => ({
          recentSearches: state.recentSearches.filter((r) => r.id !== id),
        })),
      setLoading: (v) => set({ isLoading: v }),
      setError: (e) => set({ error: e, isLoading: false }),
      reset: () => set({ weatherData: null, isLoading: false, error: null }),
    }),
    {
      name: "weather-store",
      storage: createJSONStorage(() =>
        typeof window !== "undefined"
          ? sessionStorage
          : { getItem: () => null, setItem: () => {}, removeItem: () => {} }
      ),
    }
  )
);
