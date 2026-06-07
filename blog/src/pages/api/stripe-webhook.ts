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
