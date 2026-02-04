export async function onRequest({ params, env, request }) {
  const key = (params.path || []).join("/")

  // Main /apps page - serve static apps.html (R2_APPS may not be configured)
  if (!key || key === "") {
    if (env.ASSETS) {
      return env.ASSETS.fetch(new URL("/apps.html", request.url))
    }
    return new Response("Apps page not available", { status: 503 })
  }

  // Subpaths - require R2_APPS
  if (!env.R2_APPS) {
    return new Response("Apps storage not configured", { status: 503 })
  }

  try {
    const object = await env.R2_APPS.get(`apps/${key}`)

    if (!object) {
      return new Response("Not found", { status: 404 })
    }

    return new Response(object.body, {
      headers: {
        "Content-Type": object.httpMetadata?.contentType || "application/octet-stream",
        "Cache-Control": "public, max-age=31536000, immutable"
      }
    })
  } catch (err) {
    return new Response("Error loading app: " + err.message, { status: 500 })
  }
}

