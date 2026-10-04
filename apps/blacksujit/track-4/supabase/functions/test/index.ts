// Minimal test function
export default async function handler(req: Request) {
  return new Response("OK", { 
    status: 200,
    headers: { "Content-Type": "text/plain" }
  });
}