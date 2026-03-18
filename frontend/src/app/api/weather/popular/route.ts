import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const INTERNAL_API_TOKEN = process.env.INTERNAL_API_TOKEN || "";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/weather/popular`, {
      headers: { "x-internal-token": INTERNAL_API_TOKEN },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}
