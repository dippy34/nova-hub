// Serves temp deploy URLs: GET /d/:id redirects to the deployed GitHub repo (jsDelivr) for 30 mins.
export async function onRequestGet(context) {
  const { env, params } = context;
  const id = params.id;
  if (!id) {
    return new Response('Not found', { status: 404 });
  }

  const kv = env.ANALYTICS_KV;
  if (!kv) {
    return new Response('Deploy not configured', { status: 503 });
  }

  const raw = await kv.get(`deploy:${id}`);
  if (!raw) {
    return new Response('Deploy not found or expired', { status: 404 });
  }

  let data;
  try {
    data = JSON.parse(raw);
  } catch (_) {
    return new Response('Invalid deploy', { status: 404 });
  }

  const expiresAt = new Date(data.expiresAt);
  if (expiresAt < new Date()) {
    return new Response('Deploy expired', { status: 404 });
  }

  const { owner, repo, branch, subpath } = data;
  if (!owner || !repo) {
    return new Response('Invalid deploy', { status: 404 });
  }

  const base = `https://cdn.jsdelivr.net/gh/${owner}/${repo}@${branch || 'main'}`;
  const target = subpath ? `${base}/${subpath}/` : `${base}/`;
  return Response.redirect(target, 302);
}
