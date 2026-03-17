import { WeatherResponse } from "@/types/weather";

export const weatherClient = {
  fetchByCity: async (city: string, country?: string): Promise<WeatherResponse> => {
    const res = await fetch("/api/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "city", city, country: country ?? "" }),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Failed to fetch weather");
    }
    return res.json();
  },

  fetchByCoords: async (latitude: number, longitude: number): Promise<WeatherResponse> => {
    const res = await fetch("/api/weather", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: "coords", latitude, longitude }),
    });
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || "Failed to fetch weather");
    }
    return res.json();
  },
};
