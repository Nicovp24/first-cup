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

  if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error('subscribe: missing Supabase env vars');
    return reply({ message: 'Error de configuración.' }, 500);
  }

  // ── Save to Supabase ──
  const sbRes = await fetch(`${SUPABASE_URL}/rest/v1/subscribers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'apikey': SUPABASE_KEY,
      'Authorization': `Bearer ${SUPABASE_KEY}`,
      'Prefer': 'return=minimal',
    },
    body: JSON.stringify({ email }),
  });

  if (!sbRes.ok) {
    const err = await sbRes.json().catch(() => ({})) as Record<string, unknown>;
    if (sbRes.status === 409 || err?.code === '23505') {
      // unique violation — already subscribed, treat as success to avoid enumeration
      return reply({ ok: true }, 200);
    }
    console.error('Supabase subscribe error:', err);
    return reply({ message: 'No se pudo guardar la suscripción.' }, 500);
  }

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
          subject: '☕ Bienvenido a First Cup',
          html: welcomeHtml(),
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

function welcomeHtml(): string {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body  { margin:0; padding:0; background:#f5f0e8; font-family:Georgia,'Times New Roman',serif; color:#2a1f14; }
    table { border-collapse:collapse; }
    a     { color:#8b4513; }
  </style>
</head>
<body>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e8; padding:2rem 1rem;">
    <tr><td>
      <table width="560" align="center" cellpadding="0" cellspacing="0"
             style="max-width:560px; width:100%; margin:0 auto; background:#f5f0e8;">

        <!-- Header -->
        <tr><td style="border-top:3px solid #1a0f06; border-bottom:1px solid #c5a882;
                        padding:1.25rem 0; text-align:center;">
          <span style="display:block; font-family:monospace; font-size:0.6rem;
                        letter-spacing:0.2em; text-transform:uppercase; color:#8b4513;
                        margin-bottom:0.4rem;">EST. MMXXVI · La Gaceta Digital</span>
          <span style="font-size:2.4rem; font-weight:900; color:#1a0f06;
                        font-family:Georgia,serif; letter-spacing:-0.02em;">First Cup</span>
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:2rem 0 1rem;">

          <span style="font-family:monospace; font-size:0.62rem; letter-spacing:0.18em;
                        text-transform:uppercase; color:#8b4513;">Bienvenido al digest</span>

          <h1 style="font-family:Georgia,serif; font-size:1.6rem; font-weight:700;
                      color:#1a0f06; margin:0.75rem 0 1rem; line-height:1.2;
                      letter-spacing:-0.01em;">El café está en camino.</h1>

          <p style="font-size:1rem; line-height:1.75; color:#4a3728; margin:0 0 1.1rem;">
            A partir de ahora recibirás el mejor tech de cada mañana — IA, desarrollo y
            tendencias seleccionadas automáticamente por un agente que no duerme.
          </p>

          <p style="font-size:0.95rem; line-height:1.7; color:#4a3728; margin:0 0 0.5rem;
                     font-weight:700;">Lo que encontrarás en cada edición:</p>

          <ul style="padding-left:1.4rem; margin:0 0 1.5rem;">
            <li style="margin-bottom:0.5rem; line-height:1.65; color:#4a3728; font-size:0.95rem;">
              Los repos más interesantes de GitHub Trending
            </li>
            <li style="margin-bottom:0.5rem; line-height:1.65; color:#4a3728; font-size:0.95rem;">
              Los papers de IA que importan esta semana
            </li>
            <li style="margin-bottom:0.5rem; line-height:1.65; color:#4a3728; font-size:0.95rem;">
              Lo que la comunidad tech discute en Hacker News
            </li>
            <li style="margin-bottom:0.5rem; line-height:1.65; color:#4a3728; font-size:0.95rem;">
              Lanzamientos y tendencias que cambian cómo programamos
            </li>
          </ul>

          <!-- CTA -->
          <a href="https://firstcup.dev"
             style="display:block; background:#8b4513; color:#f5f0e8; text-align:center;
                     text-decoration:none; font-family:monospace; font-size:0.78rem;
                     font-weight:700; letter-spacing:0.12em; text-transform:uppercase;
                     padding:0.95rem 2rem; margin:1.75rem 0;">
            Ver el último digest →
          </a>

          <p style="font-style:italic; font-size:0.88rem; color:#6b5744;
                     line-height:1.65; margin:0;">
            Publicamos cada mañana antes de las 8h, listo para leer con el café.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td style="border-top:1px solid #c5a882; padding-top:1.25rem; margin-top:2rem;">
          <p style="font-family:monospace; font-size:0.62rem; color:#9a8572;
                     letter-spacing:0.06em; margin:0 0 0.4rem;">
            © 2026 First Cup ·
            <a href="https://firstcup.dev" style="color:#8b4513; text-decoration:none;">
              firstcup.dev
            </a>
          </p>
          <p style="font-family:monospace; font-size:0.6rem; color:#b0a090;
                     letter-spacing:0.04em; margin:0; line-height:1.6;">
            Has recibido este email porque te suscribiste en firstcup.dev.<br/>
            Para darte de baja, responde con "baja" a este correo.
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;
}
