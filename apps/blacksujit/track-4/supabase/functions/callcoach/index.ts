// Minimal Supabase Edge Function
export default async function handler(req: Request) {
  const url = new URL(req.url);
  
  // CORS headers
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  };

  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers });
  }

  if (url.pathname === "/api/health") {
    return new Response(JSON.stringify({
      status: "ok",
      platform: "supabase-edge-function",
      timestamp: new Date().toISOString()
    }), { 
      status: 200, 
      headers: { ...headers, "Content-Type": "application/json" } 
    });
  }

  // List jobs
  if (url.pathname === "/api/jobs" && req.method === "GET") {
    return new Response(JSON.stringify({ jobs: [] }), {
      status: 200,
      headers: { ...headers, "Content-Type": "application/json" }
    });
  }

  // Settings
  if (url.pathname === "/api/settings" && req.method === "POST") {
    return new Response(JSON.stringify({ 
      message: "Settings saved",
      whipscribe_key_set: true
    }), {
      status: 200,
      headers: { ...headers, "Content-Type": "application/json" }
    });
  }

  // List recordings endpoint (stub)
  return new Response(JSON.stringify({
    error: "Not found",
    path: url.pathname,
    method: req.method
  }), {
    status: 404,
    headers: { ...headers, "Content-Type": "application/json" }
  });
}