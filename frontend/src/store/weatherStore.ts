import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { WeatherResponse } from "@/types/weather";

interface WeatherStore {
  weatherData: WeatherResponse | null;
  isLoading: boolean;
  error: string | null;
  setWeatherData: (data: WeatherResponse) => void;
  setLoading: (v: boolean) => void;
  setError: (e: string | null) => void;
  reset: () => void;
}

export const useWeatherStore = create<WeatherStore>()(
  persist(
    (set) => ({
      weatherData: null,
      isLoading: false,
      error: null,
      setWeatherData: (data) => set({ weatherData: data, error: null }),
      setLoading: (v) => set({ isLoading: v }),
      setError: (e) => set({ error: e, isLoading: false }),
      reset: () => set({ weatherData: null, isLoading: false, error: null }),
    }),
    {
      name: "weather-store",
      storage: createJSONStorage(() =>
        typeof window !== "undefined" ? sessionStorage : { getItem: () => null, setItem: () => {}, removeItem: () => {} }
      ),
    }
  )
);
