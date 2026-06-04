import type { APIRoute } from 'astro';

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json() as { email?: unknown };
    const email = typeof body.email === 'string' ? body.email.trim() : '';

    // Basic validation
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response(
        JSON.stringify({ ok: false, message: 'Email inválido.' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // TODO: integrate with your email provider (ConvertKit, Resend, Supabase, etc.)
    // Example with a generic HTTP POST:
    //
    // const WEBHOOK_URL = import.meta.env.SUBSCRIBE_WEBHOOK_URL;
    // if (WEBHOOK_URL) {
    //   await fetch(WEBHOOK_URL, {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ email }),
    //   });
    // }

    console.log(`[subscribe] new subscriber: ${email}`);

    return new Response(
      JSON.stringify({ ok: true, message: 'Suscripción registrada.' }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err) {
    console.error('[subscribe] error:', err);
    return new Response(
      JSON.stringify({ ok: false, message: 'Error interno del servidor.' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
