// Vercel Serverless Function - Proxy to Render backend
// Handles CORS, timeouts, and error cases

const BACKEND_URL = process.env.BACKEND_URL || 'https://callcoach-ai-whhipscribe.onrender.com';
const TIMEOUT_MS = 60000;

export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  try {
    const url = new URL(req.url);
    const path = url.pathname.replace('/api', '') || '/';
    const backendUrl = `${BACKEND_URL}${path}${url.search}`;

    const response = await fetch(backendUrl, {
      method: req.method,
      headers: {
        'Content-Type': req.headers['content-type'] || 'application/json',
        'X-API-Key': req.headers['x-api-key'] || '',
      },
      body: ['GET', 'HEAD', 'OPTIONS'].includes(req.method) ? undefined : req.body,
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });

    const data = await response.text();
    res.status(response.status);
    res.setHeader('Content-Type', response.headers.get('content-type') || 'application/json');
    res.send(data);
  } catch (error) {
    res.status(502).json({
      error: 'Backend service temporarily unavailable',
      details: error.message,
      service: 'callcoach-api-proxy',
      timestamp: new Date().toISOString()
    });
  }
}
