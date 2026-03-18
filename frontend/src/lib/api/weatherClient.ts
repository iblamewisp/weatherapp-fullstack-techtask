import { WeatherResponse } from "@/types/weather";

const BASE = "/api/weather";

export const weatherClient = {
  fetchByCity: async (city: string, country: string): Promise<WeatherResponse> => {
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city, country }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to fetch weather");
    }
    return res.json();
  },

  fetchByCoords: async (latitude: number, longitude: number): Promise<WeatherResponse> => {
    const res = await fetch(BASE, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ latitude, longitude }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to fetch weather");
    }
    return res.json();
  },

  getAll: async (): Promise<WeatherResponse[]> => {
    const res = await fetch(BASE);
    if (!res.ok) throw new Error("Failed to fetch weather list");
    return res.json();
  },

  createRecord: async (data: Partial<WeatherResponse>): Promise<WeatherResponse> => {
    const res = await fetch(`${BASE}/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create record");
    }
    return res.json();
  },

  getPopular: async (): Promise<WeatherResponse[]> => {
    const res = await fetch(`${BASE}/popular`);
    if (!res.ok) throw new Error("Failed to fetch popular cities");
    return res.json();
  },

  updateById: async (id: string, data: Partial<WeatherResponse>): Promise<WeatherResponse> => {
    const res = await fetch(`${BASE}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to update weather");
    }
    return res.json();
  },

  deleteById: async (id: string): Promise<void> => {
    const res = await fetch(`${BASE}/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete weather record");
  },
};
