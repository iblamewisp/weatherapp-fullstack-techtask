"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useWeatherStore } from "@/store/weatherStore";
import { WeatherResult } from "@/components/WeatherResult";

export default function ResultPage() {
  const router = useRouter();
  const { weatherData, isLoading } = useWeatherStore();

  useEffect(() => {
    if (!weatherData && !isLoading) {
      router.push("/");
    }
  }, [weatherData, isLoading, router]);

  if (!weatherData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return <WeatherResult weather={weatherData} />;
}
