import type { APIRoute } from 'astro';

export const prerender = false;

export const POST: APIRoute = async ({ request }) => {
  const STRIPE_WEBHOOK_SECRET = import.meta.env.STRIPE_WEBHOOK_SECRET;
  const SUPABASE_URL          = import.meta.env.SUPABASE_URL;
  const SUPABASE_KEY          = import.meta.env.SUPABASE_SERVICE_KEY;

  if (!STRIPE_WEBHOOK_SECRET || !SUPABASE_URL || !SUPABASE_KEY) {
    console.error('stripe-webhook: missing env vars');
    return new Response('Configuration error', { status: 500 });
  }

  const sigHeader = request.headers.get('stripe-signature');
  if (!sigHeader) {
    return new Response('Missing Stripe-Signature', { status: 400 });
  }

  // Read raw body as text (needed for signature verification)
  const rawBody = await request.text();

  // Verify Stripe signature using Web Crypto API (no SDK required)
  const valid = await verifyStripeSignature(rawBody, sigHeader, STRIPE_WEBHOOK_SECRET);
  if (!valid) {
    console.error('stripe-webhook: invalid signature');
    return new Response('Invalid signature', { status: 400 });
  }

  let event: StripeEvent;
  try {
    event = JSON.parse(rawBody) as StripeEvent;
  } catch {
    return new Response('Invalid JSON', { status: 400 });
  }

  // Handle relevant events
  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;
    const email   = session.customer_email ?? session.customer_details?.email ?? '';

    if (email) {
      try {
        // Update subscriber tier to premium + store Stripe customer ID
        await fetch(
          `${SUPABASE_URL}/rest/v1/subscribers?email=eq.${encodeURIComponent(email)}`,
          {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'apikey': SUPABASE_KEY,
              'Authorization': `Bearer ${SUPABASE_KEY}`,
              'Prefer': 'return=minimal',
            },
            body: JSON.stringify({
              tier: 'premium',
              confirmed: true,
              stripe_id: session.customer ?? null,
            }),
          }
        );

        // Also upsert in case they weren't subscribed yet (paid directly)
        await fetch(`${SUPABASE_URL}/rest/v1/subscribers`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'apikey': SUPABASE_KEY,
            'Authorization': `Bearer ${SUPABASE_KEY}`,
            'Prefer': 'resolution=merge-duplicates,return=minimal',
          },
          body: JSON.stringify({
            email,
            tier: 'premium',
            confirmed: true,
            stripe_id: session.customer ?? null,
            confirm_token: crypto.randomUUID(),
          }),
        });

        console.log(`stripe-webhook: upgraded ${email} to premium`);

        // Send Premium welcome email — awaited so Vercel doesn't kill it early
        const RESEND_KEY = import.meta.env.RESEND_API_KEY;
        const EMAIL_FROM = import.meta.env.EMAIL_FROM ?? 'First Cup <hola@first-cup.es>';
        if (RESEND_KEY) {
          try {
            const wr = await fetch('https://api.resend.com/emails', {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${RESEND_KEY}`, 'Content-Type': 'application/json' },
              body: JSON.stringify({
                from: EMAIL_FROM,
                to: [email],
                subject: '☕ Bienvenido a First Cup Premium',
                html: welcomePremiumHtml(email),
              }),
            });
            if (!wr.ok) console.error('stripe-webhook: premium welcome email failed', wr.status);
          } catch (err) {
            console.error('stripe-webhook: premium welcome email error', err);
          }
        }
      } catch (err) {
        console.error('stripe-webhook: Supabase update failed', err);
        // Return 200 anyway — Stripe will retry on non-2xx
      }
    }
  }

  if (event.type === 'customer.subscription.deleted') {
    // Downgrade back to free when subscription is cancelled
    const subscription = event.data.object;
    const customerId   = subscription.customer;

    if (customerId) {
      try {
        await fetch(
          `${SUPABASE_URL}/rest/v1/subscribers?stripe_id=eq.${encodeURIComponent(customerId)}`,
          {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
              'apikey': SUPABASE_KEY,
              'Authorization': `Bearer ${SUPABASE_KEY}`,
              'Prefer': 'return=minimal',
            },
            body: JSON.stringify({ tier: 'free' }),
          }
        );
        console.log(`stripe-webhook: downgraded customer ${customerId} to free`);
      } catch (err) {
        console.error('stripe-webhook: downgrade failed', err);
      }
    }
  }

  return new Response(JSON.stringify({ received: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
};

// ---------------------------------------------------------------------------
// Stripe signature verification (HMAC-SHA256 via Web Crypto API)
// ---------------------------------------------------------------------------

async function verifyStripeSignature(
  payload: string,
  sigHeader: string,
  secret: string
): Promise<boolean> {
  try {
    // Parse timestamp and v1 signatures from the header
    const parts: Record<string, string[]> = {};
    for (const chunk of sigHeader.split(',')) {
      const eq = chunk.indexOf('=');
      if (eq === -1) continue;
      const k = chunk.slice(0, eq).trim();
      const v = chunk.slice(eq + 1).trim();
      if (!parts[k]) parts[k] = [];
      parts[k].push(v);
    }

    const timestamp = parts['t']?.[0];
    const v1Sigs    = parts['v1'] ?? [];

    if (!timestamp || v1Sigs.length === 0) return false;

    // Reject events older than 5 minutes (replay protection)
    if (Math.abs(Date.now() / 1000 - Number(timestamp)) > 300) return false;

    const signedPayload = `${timestamp}.${payload}`;

    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );

    const sigBytes = await crypto.subtle.sign(
      'HMAC',
      key,
      new TextEncoder().encode(signedPayload)
    );

    const hexSig = Array.from(new Uint8Array(sigBytes))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');

    return v1Sigs.includes(hexSig);
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Premium welcome email
// ---------------------------------------------------------------------------

function welcomePremiumHtml(email: string): string {
  const site = 'https://first-cup.es';
  return `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f5f0e8;font-family:Georgia,serif;color:#1a0f06;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e8;padding:2rem 1rem;">
<tr><td><table width="560" align="center" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;margin:0 auto;">
  <tr><td style="border-top:3px solid #1a0f06;border-bottom:1px solid #c5a882;padding:1.5rem 0;text-align:center;">
    <span style="font-family:monospace;font-size:0.55rem;letter-spacing:0.22em;text-transform:uppercase;color:#8b4513;display:block;margin-bottom:0.4rem;">Suscriptor Premium</span>
    <span style="font-size:2.4rem;font-weight:900;color:#1a0f06;font-family:Georgia,serif;letter-spacing:-0.02em;">First Cup</span>
    <span style="display:block;font-family:monospace;font-size:0.52rem;letter-spacing:0.18em;text-transform:uppercase;color:#9a8572;margin-top:0.4rem;">IA · Desarrollo · Tecnología</span>
  </td></tr>
  <tr><td style="padding:2rem 0;">
    <p style="font-size:1.05rem;line-height:1.7;color:#1a0f06;margin:0 0 1rem;font-weight:700;">Ya eres Premium. Bienvenido.</p>
    <p style="font-size:0.95rem;line-height:1.7;color:#4a3728;margin:0 0 0.75rem;">A partir de mañana recibirás:</p>
    <table cellpadding="0" cellspacing="0" style="margin-bottom:1.5rem;">
      <tr><td style="padding:0.3rem 0;font-size:0.92rem;color:#4a3728;">☕ &nbsp;<strong>Digest diario</strong> — 6 artículos cada mañana a las 07:00</td></tr>
      <tr><td style="padding:0.3rem 0;font-size:0.92rem;color:#4a3728;">⚡ &nbsp;<strong>Shots del día</strong> — micro-dosis de lo que también pasó</td></tr>
      <tr><td style="padding:0.3rem 0;font-size:0.92rem;color:#4a3728;">🔴 &nbsp;<strong>Breaking news</strong> — alertas instantáneas cuando algo es urgente</td></tr>
      <tr><td style="padding:0.3rem 0;font-size:0.92rem;color:#4a3728;">📋 &nbsp;<strong>Resumen semanal</strong> — lo mejor de la semana, cada domingo</td></tr>
    </table>
    <table cellpadding="0" cellspacing="0"><tr><td>
      <a href="${site}" style="display:inline-block;background:#8b4513;color:#f5f0e8;
         text-decoration:none;font-family:monospace;font-size:0.7rem;font-weight:700;
         letter-spacing:0.14em;text-transform:uppercase;padding:0.75rem 1.75rem;">
        Ir a First Cup →
      </a>
    </td></tr></table>
  </td></tr>
  <tr><td style="border-top:1px solid #c5a882;padding:1rem 0;text-align:center;">
    <p style="font-family:monospace;font-size:0.58rem;color:#9a8572;margin:0 0 0.25rem;">
      © 2026 First Cup · <a href="${site}" style="color:#8b4513;text-decoration:none;">first-cup.es</a>
    </p>
    <p style="font-family:monospace;font-size:0.54rem;color:#b0a090;margin:0;">
      <a href="${site}/cuenta" style="color:#b0a090;">Gestionar suscripción</a>
    </p>
  </td></tr>
</table></td></tr></table>
</body></html>`;
}

// ---------------------------------------------------------------------------
// Minimal Stripe event types
// ---------------------------------------------------------------------------

interface StripeEvent {
  type: string;
  data: {
    object: {
      customer?: string | null;
      customer_email?: string | null;
      customer_details?: { email?: string | null } | null;
    };
  };
}
