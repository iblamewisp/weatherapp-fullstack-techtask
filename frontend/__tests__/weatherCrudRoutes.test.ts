/**
 * @jest-environment node
 */
import { NextRequest } from "next/server";
import { POST as createPost } from "../src/app/api/weather/create/route";
import { PUT, DELETE } from "../src/app/api/weather/[id]/route";

const mockWeather = {
  id: "11111111-1111-1111-1111-111111111111",
  city: "London",
  country: "GB",
  temperature: 15.0,
  last_updated: new Date().toISOString(),
  created_at: new Date().toISOString(),
};

const VALID_ID = "11111111-1111-1111-1111-111111111111";
const INVALID_ID = "not-a-uuid";

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
// POST /api/weather/create — proxies to backend POST /api/v1/weather
// ---------------------------------------------------------------------------

describe("POST /api/weather/create", () => {
  it("returns 201 with created record on success", async () => {
    mockFetch(mockWeather, 201);
    const req = new NextRequest("http://localhost/api/weather/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city: "London", country: "GB" }),
    });
    const res = await createPost(req);
    expect(res.status).toBe(201);
    const data = await res.json();
    expect(data.city).toBe("London");
  });

  it("forwards backend validation error to client", async () => {
    mockFetch({ detail: "Validation error" }, 422);
    const req = new NextRequest("http://localhost/api/weather/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city: "", country: "GB" }),
    });
    const res = await createPost(req);
    expect(res.status).toBe(422);
  });

  it("returns 500 when backend fetch throws", async () => {
    global.fetch = jest.fn().mockRejectedValueOnce(new Error("network error"));
    const req = new NextRequest("http://localhost/api/weather/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city: "London", country: "GB" }),
    });
    const res = await createPost(req);
    expect(res.status).toBe(500);
  });
});

// ---------------------------------------------------------------------------
// PUT /api/weather/[id]
// ---------------------------------------------------------------------------

describe("PUT /api/weather/[id]", () => {
  it("returns 200 with updated record", async () => {
    mockFetch({ ...mockWeather, temperature: 20.0 }, 200);
    const req = new NextRequest(`http://localhost/api/weather/${VALID_ID}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ temperature: 20.0 }),
    });
    const res = await PUT(req, { params: { id: VALID_ID } });
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.temperature).toBe(20.0);
  });

  it("returns 400 for invalid UUID", async () => {
    const req = new NextRequest(`http://localhost/api/weather/${INVALID_ID}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ temperature: 20.0 }),
    });
    const res = await PUT(req, { params: { id: INVALID_ID } });
    expect(res.status).toBe(400);
  });

  it("forwards 404 when record not found", async () => {
    mockFetch({ detail: "Not found" }, 404);
    const req = new NextRequest(`http://localhost/api/weather/${VALID_ID}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ temperature: 20.0 }),
    });
    const res = await PUT(req, { params: { id: VALID_ID } });
    expect(res.status).toBe(404);
  });
});

// ---------------------------------------------------------------------------
// DELETE /api/weather/[id]
// ---------------------------------------------------------------------------

describe("DELETE /api/weather/[id]", () => {
  it("returns 204 on success", async () => {
    global.fetch = jest.fn().mockResolvedValueOnce({ status: 204, ok: true });
    const req = new NextRequest(`http://localhost/api/weather/${VALID_ID}`, {
      method: "DELETE",
    });
    const res = await DELETE(req, { params: { id: VALID_ID } });
    expect(res.status).toBe(204);
  });

  it("returns 400 for invalid UUID", async () => {
    const req = new NextRequest(`http://localhost/api/weather/${INVALID_ID}`, {
      method: "DELETE",
    });
    const res = await DELETE(req, { params: { id: INVALID_ID } });
    expect(res.status).toBe(400);
  });

  it("forwards 404 when record not found", async () => {
    mockFetch({ detail: "Not found" }, 404);
    const req = new NextRequest(`http://localhost/api/weather/${VALID_ID}`, {
      method: "DELETE",
    });
    const res = await DELETE(req, { params: { id: VALID_ID } });
    expect(res.status).toBe(404);
  });
});
