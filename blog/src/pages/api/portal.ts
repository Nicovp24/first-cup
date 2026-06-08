import type { APIRoute } from 'astro';

export const prerender = false;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const POST: APIRoute = async ({ request }) => {
  let email: string;
  try {
    const body = await request.json();
    email = (body?.email ?? '').trim().toLowerCase();
  } catch {
    return reply({ message: 'Solicitud inválida.' }, 400);
  }

  if (!email || !EMAIL_RE.test(email)) {
    return reply({ message: 'Introduce un email válido.' }, 400);
  }

  const STRIPE_KEY    = import.meta.env.STRIPE_SECRET_KEY;
  const SUPABASE_URL  = import.meta.env.SUPABASE_URL;
  const SUPABASE_KEY  = import.meta.env.SUPABASE_SERVICE_KEY;
  const SITE          = (import.meta.env.SITE ?? 'https://first-cup.es').replace(/\/$/, '');

  if (!STRIPE_KEY || !SUPABASE_URL || !SUPABASE_KEY) {
    return reply({ message: 'Error de configuración.' }, 500);
  }

  // Look up stripe_id for this email
  const sbRes = await fetch(
    `${SUPABASE_URL}/rest/v1/subscribers?email=eq.${encodeURIComponent(email)}&select=stripe_id,tier`,
    {
      headers: {
        'apikey': SUPABASE_KEY,
        'Authorization': `Bearer ${SUPABASE_KEY}`,
      },
    }
  );

  const rows = await sbRes.json().catch(() => []) as Array<{ stripe_id?: string; tier?: string }>;
  const row  = rows?.[0];

  if (!row?.stripe_id) {
    return reply({ message: 'No encontramos una suscripción Premium activa con ese email.' }, 404);
  }

  // Create Stripe Customer Portal session
  const params = new URLSearchParams({
    customer:       row.stripe_id,
    return_url:     `${SITE}/`,
  });

  const portalRes = await fetch('https://api.stripe.com/v1/billing_portal/sessions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${STRIPE_KEY}`,
      'Content-Type':  'application/x-www-form-urlencoded',
    },
    body: params.toString(),
  });

  if (!portalRes.ok) {
    const err = await portalRes.json().catch(() => ({}));
    console.error('Stripe portal error:', err);
    return reply({ message: 'Error al abrir el portal. Escríbenos a hola@first-cup.es' }, 500);
  }

  const session = await portalRes.json() as { url: string };
  return reply({ url: session.url }, 200);
};

function reply(body: object, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
