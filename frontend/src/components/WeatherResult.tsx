"use client";
import Image from "next/image";
import { WeatherResponse } from "@/types/weather";
import { useRouter } from "next/navigation";

interface Props {
  weather: WeatherResponse;
}

function getBgColor(temp: number | null): string {
  if (temp === null) return "#2d6a9f";
  if (temp < 0) return "#1a3a5c";
  if (temp < 10) return "#2d6a9f";
  if (temp < 20) return "#2d9f7a";
  if (temp < 30) return "#e8a020";
  return "#d44c30";
}

function getTextColor(temp: number | null): string {
  if (temp === null) return "#ffffff";
  if (temp < 20) return "#ffffff";
  if (temp < 30) return "#1a1a1a";
  return "#ffffff";
}

export function WeatherResult({ weather }: Props) {
  const router = useRouter();
  const bgColor = getBgColor(weather.temperature);
  const textColor = getTextColor(weather.temperature);

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-6"
      style={{ backgroundColor: bgColor, color: textColor }}
    >
      <div className="max-w-md w-full rounded-2xl p-8 shadow-2xl" style={{ backgroundColor: "rgba(0,0,0,0.15)" }}>
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold">
            {weather.city}, {weather.country}
          </h1>
          {weather.weather_icon && (
            <Image
              src={`https://openweathermap.org/img/wn/${weather.weather_icon}@2x.png`}
              alt={weather.weather_description || "weather icon"}
              className="mx-auto"
              width={80}
              height={80}
            />
          )}
          <p className="text-6xl font-extrabold mt-2">
            {weather.temperature !== null ? `${Math.round(weather.temperature)}°C` : "N/A"}
          </p>
          <p className="text-lg capitalize mt-1 opacity-90">{weather.weather_description}</p>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="rounded-lg p-3" style={{ backgroundColor: "rgba(0,0,0,0.1)" }}>
            <p className="opacity-75">Feels like</p>
            <p className="font-semibold text-lg">
              {weather.feels_like !== null ? `${Math.round(weather.feels_like)}°C` : "N/A"}
            </p>
          </div>
          <div className="rounded-lg p-3" style={{ backgroundColor: "rgba(0,0,0,0.1)" }}>
            <p className="opacity-75">Humidity</p>
            <p className="font-semibold text-lg">{weather.humidity !== null ? `${weather.humidity}%` : "N/A"}</p>
          </div>
          <div className="rounded-lg p-3" style={{ backgroundColor: "rgba(0,0,0,0.1)" }}>
            <p className="opacity-75">Pressure</p>
            <p className="font-semibold text-lg">{weather.pressure !== null ? `${weather.pressure} hPa` : "N/A"}</p>
          </div>
          <div className="rounded-lg p-3" style={{ backgroundColor: "rgba(0,0,0,0.1)" }}>
            <p className="opacity-75">Wind Speed</p>
            <p className="font-semibold text-lg">{weather.wind_speed !== null ? `${weather.wind_speed} m/s` : "N/A"}</p>
          </div>
        </div>

        <p className="text-xs opacity-60 text-center mt-6">
          Last updated: {new Date(weather.last_updated).toLocaleString()}
        </p>

        <button
          onClick={() => router.push("/")}
          className="mt-6 w-full py-2 px-4 rounded-lg font-medium transition-colors"
          style={{ backgroundColor: "rgba(255,255,255,0.2)", color: textColor }}
        >
          Search Again
        </button>
      </div>
    </div>
  );
}
