export async function onRequest({ params, env }) {
  const key = params.path.join("/")

  const object = await env.semag.get(`semag/${key}`)

  if (!object) {
    return new Response("Not found", { status: 404 })
  }

  return new Response(object.body, {
    headers: {
      "Content-Type": object.httpMetadata?.contentType || "application/octet-stream",
      "Cache-Control": "public, max-age=31536000, immutable"
    }
  })
}