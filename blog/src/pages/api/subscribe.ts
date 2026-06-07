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

  const SUPABASE_URL  = import.meta.env.SUPABASE_URL;
  const SUPABASE_KEY  = import.meta.env.SUPABASE_SERVICE_KEY;
  const RESEND_KEY    = import.meta.env.RESEND_API_KEY;
  const EMAIL_FROM    = import.meta.env.EMAIL_FROM || 'First Cup <hola@firstcup.es>';
  const SITE          = (import.meta.env.SITE ?? 'https://first-cup-kappa.vercel.app').replace(/\/$/, '');

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error('subscribe: missing Supabase env vars');
    return reply({ message: 'Error de configuración.' }, 500);
  }

  // Generate a unique confirmation token
  const confirmToken = crypto.randomUUID();

  // ── Save to Supabase (with confirm token) ──
  const sbRes = await fetch(`${SUPABASE_URL}/rest/v1/subscribers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
      'Prefer': 'return=minimal',
    },
    body: JSON.stringify({ email, confirm_token: confirmToken, confirmed: false }),
  });

  if (!sbRes.ok) {
    const err = await sbRes.json().catch(() => ({})) as Record<string, unknown>;
    if (sbRes.status === 409 || err?.code === '23505') {
      // Already subscribed — still send them back a success (no enumeration)
      return reply({ ok: true }, 200);
    }
    const errMsg = String(err?.message ?? err?.error ?? `HTTP ${sbRes.status}`);
    console.error('Supabase subscribe error:', sbRes.status, err);
    return reply({ message: `Error Supabase: ${errMsg}` }, 500);
  }

  const confirmUrl     = `${SITE}/api/confirm?token=${confirmToken}`;
  const unsubscribeUrl = `${SITE}/api/unsubscribe?token=${confirmToken}`;

  // ── Welcome email via Resend (non-fatal if it fails) ──
  if (RESEND_KEY) {
    try {
      const emailRes = await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${RESEND_KEY}`,
        },
        body: JSON.stringify({
          from: EMAIL_FROM,
          to: [email],
          subject: '☕ Confirma tu suscripción a First Cup',
          html: welcomeHtml(confirmUrl, unsubscribeUrl, SITE),
        }),
      });
      if (!emailRes.ok) {
        const resendErr = await emailRes.json().catch(() => ({}));
        console.error('Resend error (non-fatal):', resendErr);
      }
    } catch (err) {
      console.error('Resend fetch error (non-fatal):', err);
    }
  }

  return reply({ ok: true }, 200);
};

function reply(body: object, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function welcomeHtml(confirmUrl: string, unsubscribeUrl: string, site: string): string {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <style>
    body{margin:0;padding:0;background:#f5f0e8;font-family:Georgia,'Times New Roman',serif;color:#2a1f14;}
    table{border-collapse:collapse;}
    a{color:#8b4513;}
  </style>
</head>
<body>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e8;padding:2rem 1rem;">
    <tr><td>
      <table width="560" align="center" cellpadding="0" cellspacing="0"
             style="max-width:560px;width:100%;margin:0 auto;background:#f5f0e8;">

        <!-- Header -->
        <tr><td style="border-top:3px solid #1a0f06;border-bottom:1px solid #c5a882;
                        padding:1.25rem 0;text-align:center;">
          <span style="display:block;font-family:monospace;font-size:0.6rem;
                        letter-spacing:0.2em;text-transform:uppercase;color:#8b4513;
                        margin-bottom:0.4rem;">EST. MMXXVI · La Gaceta Digital</span>
          <span style="font-size:2.4rem;font-weight:900;color:#1a0f06;
                        font-family:Georgia,serif;letter-spacing:-0.02em;">First Cup</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:2rem 0 1rem;">
          <span style="font-family:monospace;font-size:0.62rem;letter-spacing:0.18em;
                        text-transform:uppercase;color:#8b4513;">Un paso más</span>

          <h1 style="font-family:Georgia,serif;font-size:1.6rem;font-weight:700;
                      color:#1a0f06;margin:0.75rem 0 1rem;line-height:1.2;letter-spacing:-0.01em;">
            Confirma tu suscripción.
          </h1>

          <p style="font-size:1rem;line-height:1.75;color:#4a3728;margin:0 0 1.5rem;">
            Haz clic en el botón para confirmar tu email y empezar a recibir
            el café tech de cada mañana.
          </p>

          <!-- Confirm CTA -->
          <a href="${confirmUrl}"
             style="display:block;background:#8b4513;color:#f5f0e8;text-align:center;
                     text-decoration:none;font-family:monospace;font-size:0.78rem;
                     font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                     padding:0.95rem 2rem;margin:0 0 1.5rem;">
            Confirmar suscripción →
          </a>

          <p style="font-size:0.88rem;line-height:1.7;color:#4a3728;margin:0 0 0.5rem;">
            O copia este enlace en tu navegador:
          </p>
          <p style="font-family:monospace;font-size:0.72rem;color:#6b5744;
                     word-break:break-all;margin:0 0 1.5rem;background:#ede8df;
                     padding:0.6rem 0.8rem;border-left:3px solid #8b4513;">
            ${confirmUrl}
          </p>

          <p style="font-style:italic;font-size:0.85rem;color:#6b5744;line-height:1.65;margin:0;">
            Si no te has suscrito tú, ignora este email — no pasará nada.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="border-top:1px solid #c5a882;padding-top:1.25rem;margin-top:2rem;">
          <p style="font-family:monospace;font-size:0.62rem;color:#9a8572;
                     letter-spacing:0.06em;margin:0 0 0.4rem;">
            © 2026 First Cup ·
            <a href="${site}" style="color:#8b4513;text-decoration:none;">firstcup.es</a>
          </p>
          <p style="font-family:monospace;font-size:0.6rem;color:#b0a090;
                     letter-spacing:0.04em;margin:0;line-height:1.6;">
            <a href="${unsubscribeUrl}" style="color:#b0a090;">Cancelar suscripción</a>
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;
}
