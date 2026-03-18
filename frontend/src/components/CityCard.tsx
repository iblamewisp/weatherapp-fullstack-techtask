"use client";
import Image from "next/image";
import { WeatherResponse } from "@/types/weather";

interface Props {
  weather: WeatherResponse;
  onEdit?: (weather: WeatherResponse) => void;
}

function getBgColor(temp: number | null): string {
  if (temp === null) return "#2d6a9f";
  if (temp < 0) return "#1a3a5c";
  if (temp < 10) return "#2d6a9f";
  if (temp < 20) return "#2d9f7a";
  if (temp < 30) return "#e8a020";
  return "#d44c30";
}

export function CityCard({ weather, onEdit }: Props) {
  const bg = getBgColor(weather.temperature);

  return (
    <div
      className="relative rounded-xl p-4 text-white flex flex-col gap-1 shadow-md"
      style={{ backgroundColor: bg }}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold text-sm">
          {weather.city}, {weather.country}
        </span>
        {weather.weather_icon && (
          <Image
            src={`https://openweathermap.org/img/wn/${weather.weather_icon}.png`}
            alt={weather.weather_description || "icon"}
            width={40}
            height={40}
          />
        )}
      </div>
      <p className="text-3xl font-extrabold">
        {weather.temperature !== null ? `${Math.round(weather.temperature)}°C` : "N/A"}
      </p>
      <p className="text-xs capitalize opacity-80">{weather.weather_description ?? "—"}</p>
      <p className="text-xs opacity-60 mt-1">
        {new Date(weather.last_updated).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
      </p>

      {onEdit && (
        <button
          onClick={() => onEdit(weather)}
          className="absolute bottom-2 right-2 p-1 rounded-md opacity-50 hover:opacity-100 hover:bg-white/20 transition-all"
          aria-label="Edit weather"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
        </button>
      )}
    </div>
  );
}
