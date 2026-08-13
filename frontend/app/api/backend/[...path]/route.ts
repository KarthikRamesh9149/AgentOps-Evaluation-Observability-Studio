import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.AGENTOPS_API_BASE_INTERNAL ?? "http://127.0.0.1:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const token = process.env.AGENTOPS_API_TOKEN;
  if (!token) {
    return NextResponse.json({ detail: "Backend credential is not configured" }, { status: 503 });
  }
  const { path } = await context.params;
  const target = new URL(`/${path.join("/")}`, API_BASE);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  headers.set("Authorization", `Bearer ${token}`);
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const hasBody = !["GET", "HEAD"].includes(request.method);
  const upstream = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.arrayBuffer() : undefined,
    cache: "no-store"
  });
  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: { "content-type": upstream.headers.get("content-type") ?? "application/json" }
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
