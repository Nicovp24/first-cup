import type { APIRoute } from 'astro';

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  const SUPABASE_URL = import.meta.env.SUPABASE_URL;
  const SUPABASE_KEY = import.meta.env.SUPABASE_SERVICE_KEY;

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    return new Response('Missing config', { status: 500 });
  }

  let slug = '';
  try {
    const body = await request.json();
    slug = body?.slug?.toString().trim() ?? '';
  } catch {
    return new Response('Invalid JSON', { status: 400 });
  }

  if (!slug) return new Response('Missing slug', { status: 400 });

  await fetch(`${SUPABASE_URL}/rest/v1/rpc/increment_post_view`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
    },
    body: JSON.stringify({ post_slug: slug }),
  }).catch(() => {});

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};
