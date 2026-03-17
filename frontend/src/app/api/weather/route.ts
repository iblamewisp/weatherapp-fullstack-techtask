import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const INTERNAL_API_TOKEN = process.env.INTERNAL_API_TOKEN || "";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/api/v1/weather/fetch`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-internal-token": INTERNAL_API_TOKEN,
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/weather`, {
      headers: { "x-internal-token": INTERNAL_API_TOKEN },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}
