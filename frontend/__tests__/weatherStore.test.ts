import { useWeatherStore } from "../src/store/weatherStore";
import { WeatherResponse } from "../src/types/weather";

const mockWeather: WeatherResponse = {
  id: "test-id",
  city: "London",
  country: "GB",
  latitude: 51.5,
  longitude: -0.12,
  temperature: 15.0,
  feels_like: 13.0,
  humidity: 80,
  pressure: 1013,
  wind_speed: 5.0,
  weather_description: "light rain",
  weather_icon: "10d",
  last_updated: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

describe("WeatherStore", () => {
  beforeEach(() => {
    useWeatherStore.getState().reset();
  });

  it("initial state has null weatherData", () => {
    const state = useWeatherStore.getState();
    expect(state.weatherData).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it("setWeatherData updates weatherData", () => {
    useWeatherStore.getState().setWeatherData(mockWeather);
    expect(useWeatherStore.getState().weatherData).toEqual(mockWeather);
  });

  it("setLoading updates loading state", () => {
    useWeatherStore.getState().setLoading(true);
    expect(useWeatherStore.getState().isLoading).toBe(true);
  });

  it("setError updates error and stops loading", () => {
    useWeatherStore.getState().setError("Something went wrong");
    expect(useWeatherStore.getState().error).toBe("Something went wrong");
    expect(useWeatherStore.getState().isLoading).toBe(false);
  });

  it("reset clears all state", () => {
    useWeatherStore.getState().setWeatherData(mockWeather);
    useWeatherStore.getState().setLoading(true);
    useWeatherStore.getState().reset();
    expect(useWeatherStore.getState().weatherData).toBeNull();
    expect(useWeatherStore.getState().isLoading).toBe(false);
    expect(useWeatherStore.getState().error).toBeNull();
  });
});
