/**
 * @jest-environment node
 */
import { NextRequest } from "next/server";
import { POST, GET } from "../src/app/api/weather/route";

const mockWeather = {
  id: "abc-123",
  city: "London",
  country: "GB",
  temperature: 15.0,
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

function makePostRequest(body: unknown): NextRequest {
  return new NextRequest("http://localhost/api/weather", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

afterEach(() => {
  jest.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// POST — proxies to backend /api/v1/weather/fetch
// ---------------------------------------------------------------------------

describe("POST /api/weather", () => {
  it("returns 200 with weather data on backend success", async () => {
    mockFetch(mockWeather, 200);
    const req = makePostRequest({ city: "London", country: "GB" });
    const res = await POST(req);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.city).toBe("London");
  });

  it("forwards backend error status to client", async () => {
    mockFetch({ detail: "City not found" }, 404);
    const req = makePostRequest({ city: "Unknown", country: "XX" });
    const res = await POST(req);
    expect(res.status).toBe(404);
    const data = await res.json();
    expect(data.detail).toBe("City not found");
  });

  it("returns 200 when backend sends X-Cache-Fallback (stale data)", async () => {
    mockFetch(mockWeather, 200);
    const req = makePostRequest({ city: "London", country: "GB" });
    const res = await POST(req);
    expect(res.status).toBe(200);
  });

  it("returns 500 when backend fetch throws", async () => {
    global.fetch = jest.fn().mockRejectedValueOnce(new Error("network error"));
    const req = makePostRequest({ city: "London", country: "GB" });
    const res = await POST(req);
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data.detail).toBe("Internal server error");
  });

  it("forwards x-internal-token header to backend", async () => {
    mockFetch(mockWeather, 200);
    const req = makePostRequest({ city: "London", country: "GB" });
    await POST(req);
    const calledHeaders = (fetch as jest.Mock).mock.calls[0][1].headers;
    expect(calledHeaders).toHaveProperty("x-internal-token");
  });
});

// ---------------------------------------------------------------------------
// GET — proxies to backend /api/v1/weather
// ---------------------------------------------------------------------------

describe("GET /api/weather", () => {
  it("returns list of weather records", async () => {
    mockFetch([mockWeather], 200);
    const res = await GET();
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });

  it("forwards backend error status", async () => {
    mockFetch({ detail: "Unauthorized" }, 401);
    const res = await GET();
    expect(res.status).toBe(401);
  });

  it("returns 500 when backend fetch throws", async () => {
    global.fetch = jest.fn().mockRejectedValueOnce(new Error("network error"));
    const res = await GET();
    expect(res.status).toBe(500);
    const data = await res.json();
    expect(data.detail).toBe("Internal server error");
  });
});
