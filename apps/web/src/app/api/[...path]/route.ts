import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const REQUEST_HEADERS_TO_REMOVE = [
  "accept-encoding",
  "connection",
  "content-length",
  "cookie",
  "host",
  "transfer-encoding",
];

const RESPONSE_HEADERS_TO_REMOVE = [
  "access-control-allow-credentials",
  "access-control-allow-headers",
  "access-control-allow-methods",
  "access-control-allow-origin",
  "connection",
  "content-encoding",
  "content-length",
  "transfer-encoding",
];

function upstreamBaseUrl(): string {
  return (
    process.env.TRALVANA_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://localhost:8000"
  ).replace(/\/+$/, "");
}

async function relay(request: NextRequest, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const upstreamBase = upstreamBaseUrl();
  const upstreamUrl = new URL(`${upstreamBase}/${path.join("/")}`);
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  for (const header of REQUEST_HEADERS_TO_REMOVE) {
    headers.delete(header);
  }

  const method = request.method.toUpperCase();
  const body =
    method === "GET" || method === "HEAD"
      ? undefined
      : await request.arrayBuffer();

  try {
    const upstreamResponse = await fetch(upstreamUrl, {
      method,
      headers,
      body,
      cache: "no-store",
      redirect: "manual",
    });

    const responseHeaders = new Headers(upstreamResponse.headers);
    for (const header of RESPONSE_HEADERS_TO_REMOVE) {
      responseHeaders.delete(header);
    }

    const location = responseHeaders.get("location");
    if (location) {
      const resolvedLocation = new URL(location, upstreamUrl);
      if (resolvedLocation.origin === new URL(upstreamBase).origin) {
        responseHeaders.set(
          "location",
          `/api${resolvedLocation.pathname}${resolvedLocation.search}${resolvedLocation.hash}`
        );
      }
    }

    return new Response(upstreamResponse.body, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      {
        detail:
          "Tralvana could not reach the trip-planning service. Please try again shortly.",
      },
      { status: 502 }
    );
  }
}

export const GET = relay;
export const POST = relay;
export const PUT = relay;
export const PATCH = relay;
export const DELETE = relay;
export const OPTIONS = relay;
