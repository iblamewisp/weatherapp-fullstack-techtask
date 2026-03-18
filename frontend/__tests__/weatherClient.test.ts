import { weatherClient } from "../src/lib/api/weatherClient";
import { WeatherResponse } from "../src/types/weather";

const mockWeather: WeatherResponse = {
  id: "abc-123",
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

function mockFetch(body: unknown, status = 200) {
  global.fetch = jest.fn().mockResolvedValueOnce({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValueOnce(body),
  });
}

afterEach(() => {
  jest.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// fetchByCity
// ---------------------------------------------------------------------------

describe("weatherClient.fetchByCity", () => {
  it("returns weather data on success", async () => {
    mockFetch(mockWeather);
    const result = await weatherClient.fetchByCity("London", "GB");
    expect(result).toEqual(mockWeather);
    expect(fetch).toHaveBeenCalledWith("/api/weather", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ city: "London", country: "GB" }),
    }));
  });

  it("throws with detail message on non-ok response", async () => {
    mockFetch({ detail: "City not found" }, 404);
    await expect(weatherClient.fetchByCity("Unknown", "XX")).rejects.toThrow("City not found");
  });

  it("throws fallback message when response has no detail", async () => {
    mockFetch({}, 500);
    await expect(weatherClient.fetchByCity("London", "GB")).rejects.toThrow("Failed to fetch weather");
  });

  it("throws fallback message when response body is not JSON", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 502,
      json: jest.fn().mockRejectedValueOnce(new SyntaxError("invalid json")),
    });
    await expect(weatherClient.fetchByCity("London", "GB")).rejects.toThrow("Failed to fetch weather");
  });
});

// ---------------------------------------------------------------------------
// fetchByCoords
// ---------------------------------------------------------------------------

describe("weatherClient.fetchByCoords", () => {
  it("returns weather data on success", async () => {
    mockFetch(mockWeather);
    const result = await weatherClient.fetchByCoords(51.5, -0.12);
    expect(result).toEqual(mockWeather);
    expect(fetch).toHaveBeenCalledWith("/api/weather", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ latitude: 51.5, longitude: -0.12 }),
    }));
  });

  it("throws with detail message on non-ok response", async () => {
    mockFetch({ detail: "OWM unavailable" }, 502);
    await expect(weatherClient.fetchByCoords(51.5, -0.12)).rejects.toThrow("OWM unavailable");
  });
});

// ---------------------------------------------------------------------------
// getAll
// ---------------------------------------------------------------------------

describe("weatherClient.getAll", () => {
  it("returns list of weather records", async () => {
    mockFetch([mockWeather]);
    const result = await weatherClient.getAll();
    expect(result).toEqual([mockWeather]);
    expect(fetch).toHaveBeenCalledWith("/api/weather");
  });

  it("throws on non-ok response", async () => {
    mockFetch({}, 500);
    await expect(weatherClient.getAll()).rejects.toThrow("Failed to fetch weather list");
  });
});

// ---------------------------------------------------------------------------
// deleteById
// ---------------------------------------------------------------------------

describe("weatherClient.deleteById", () => {
  it("resolves without error on 204", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({ ok: true, status: 204 });
    await expect(weatherClient.deleteById("abc-123")).resolves.toBeUndefined();
    expect(fetch).toHaveBeenCalledWith("/api/weather/abc-123", { method: "DELETE" });
  });

  it("throws on non-ok response", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({ ok: false, status: 404 });
    await expect(weatherClient.deleteById("abc-123")).rejects.toThrow("Failed to delete weather record");
  });
});
