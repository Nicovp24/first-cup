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

  const STRIPE_KEY  = import.meta.env.STRIPE_SECRET_KEY;
  const PRICE_ID    = import.meta.env.STRIPE_PREMIUM_PRICE_ID;
  const SITE        = (import.meta.env.SITE ?? 'https://first-cup-kappa.vercel.app').replace(/\/$/, '');

  if (!STRIPE_KEY || !PRICE_ID) {
    console.error('checkout: missing Stripe env vars');
    return reply({ message: 'Pagos no configurados.' }, 500);
  }

  // Create Stripe checkout session via REST API (no SDK needed)
  const params = new URLSearchParams({
    mode: 'subscription',
    'line_items[0][price]': PRICE_ID,
    'line_items[0][quantity]': '1',
    customer_email: email,
    success_url: `${SITE}/success?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${SITE}/subscribe`,
    'subscription_data[metadata][email]': email,
    'allow_promotion_codes': 'true',
  });

  try {
    const stripeRes = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${STRIPE_KEY}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    if (!stripeRes.ok) {
      const err = await stripeRes.json().catch(() => ({})) as Record<string, unknown>;
      console.error('Stripe error:', err);
      return reply({ message: 'Error al crear la sesión de pago.' }, 500);
    }

    const session = await stripeRes.json() as { url: string };
    return reply({ url: session.url }, 200);

  } catch (err) {
    console.error('Stripe fetch error:', err);
    return reply({ message: 'Error de conexión con el procesador de pagos.' }, 500);
  }
};

function reply(body: object, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
