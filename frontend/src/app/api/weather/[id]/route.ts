import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const INTERNAL_API_TOKEN = process.env.INTERNAL_API_TOKEN || "";

const headers = () => ({
  "Content-Type": "application/json",
  "x-internal-token": INTERNAL_API_TOKEN,
});

// Basic UUID format check — avoids forwarding obviously invalid requests to the backend.
const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  if (!UUID_RE.test(params.id)) {
    return NextResponse.json({ detail: "Invalid id" }, { status: 400 });
  }
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/api/v1/weather/${params.id}`, {
      method: "PUT",
      headers: headers(),
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(
  _req: NextRequest,
  { params }: { params: { id: string } }
) {
  if (!UUID_RE.test(params.id)) {
    return NextResponse.json({ detail: "Invalid id" }, { status: 400 });
  }
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/weather/${params.id}`, {
      method: "DELETE",
      headers: headers(),
    });
    if (res.status === 204) return new NextResponse(null, { status: 204 });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}
