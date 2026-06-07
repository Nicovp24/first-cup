import type { APIRoute } from 'astro';

export const prerender = false;

export const GET: APIRoute = async ({ url }) => {
  const token = url.searchParams.get('token')?.trim();

  if (!token) return redirect('/subscribe');

  const SUPABASE_URL = import.meta.env.SUPABASE_URL;
  const SUPABASE_KEY = import.meta.env.SUPABASE_SERVICE_KEY;

  if (!SUPABASE_URL || !SUPABASE_KEY) return redirect('/subscribe');

  try {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/subscribers?confirm_token=eq.${encodeURIComponent(token)}`,
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`,
          'Prefer': 'return=minimal',
        },
        body: JSON.stringify({ confirmed: true }),
      }
    );
    if (!res.ok) {
      console.error('confirm: Supabase PATCH failed', res.status);
    }
  } catch (err) {
    console.error('confirm: error', err);
  }

  return redirect('/confirmed');
};

function redirect(path: string) {
  return new Response(null, {
    status: 302,
    headers: { Location: path },
  });
}
