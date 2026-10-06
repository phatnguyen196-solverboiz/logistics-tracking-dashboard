import type { NextRequest } from "next/server";

// Runtime proxy: browser → /api/* (this Next.js server) → Django on the private address.
// Used by the single-container Render deploy. Local dev keeps calling Django directly
// through NEXT_PUBLIC_API_URL, so this route is simply unused there.
export const dynamic = "force-dynamic";

const BACKEND_URL = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  // Every Django REST endpoint ends with "/".
  const target = `${BACKEND_URL}/api/${path.map(encodeURIComponent).join("/")}/${request.nextUrl.search}`;

  const headers = new Headers({ accept: "application/json" });
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  const hasBody = request.method !== "GET" && request.method !== "HEAD";

  try {
    const upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.text() : undefined,
      cache: "no-store",
    });
    const responseHeaders = new Headers();
    const upstreamType = upstream.headers.get("content-type");
    if (upstreamType) responseHeaders.set("content-type", upstreamType);
    return new Response(await upstream.arrayBuffer(), { status: upstream.status, headers: responseHeaders });
  } catch {
    return Response.json(
      { detail: "The API is still starting up. Please retry in a few seconds." },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
