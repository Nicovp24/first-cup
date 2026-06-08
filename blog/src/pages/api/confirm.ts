import type { APIRoute } from 'astro';

export const prerender = false;

export const GET: APIRoute = async ({ url }) => {
  const token = url.searchParams.get('token')?.trim();

  if (!token) return redirect('/subscribe');

  const SUPABASE_URL = import.meta.env.SUPABASE_URL;
  const SUPABASE_KEY = import.meta.env.SUPABASE_SERVICE_KEY;

  if (!SUPABASE_URL || !SUPABASE_KEY) return redirect('/subscribe');

  let email = '';
  try {
    // Confirm in Supabase and get the subscriber's email back
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/subscribers?confirm_token=eq.${encodeURIComponent(token)}&select=email`,
      {
        headers: {
          'apikey': SUPABASE_KEY,
          'Authorization': `Bearer ${SUPABASE_KEY}`,
        },
      }
    );
    const rows = await res.json().catch(() => []) as Array<{ email: string }>;
    email = rows?.[0]?.email ?? '';

    await fetch(
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
  } catch (err) {
    console.error('confirm: error', err);
  }

  // Send free welcome email — awaited so Vercel doesn't kill the request before it completes
  if (email) {
    const RESEND_KEY = import.meta.env.RESEND_API_KEY;
    const EMAIL_FROM = import.meta.env.EMAIL_FROM ?? 'First Cup <hola@first-cup.es>';
    if (RESEND_KEY) {
      try {
        const r = await fetch('https://api.resend.com/emails', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${RESEND_KEY}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: EMAIL_FROM,
            to: [email],
            subject: '☕ Bienvenido a First Cup',
            html: welcomeFreeHtml(email),
          }),
        });
        if (!r.ok) console.error('confirm: welcome email failed', r.status, await r.text());
      } catch (err) {
        console.error('confirm: welcome email error', err);
      }
    }
  }

  return redirect('/confirmed');
};

function redirect(path: string) {
  return new Response(null, {
    status: 302,
    headers: { Location: path },
  });
}

function welcomeFreeHtml(email: string): string {
  const site = 'https://first-cup.es';
  return `<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#f5f0e8;font-family:Georgia,serif;color:#1a0f06;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f0e8;padding:2rem 1rem;">
<tr><td><table width="560" align="center" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;margin:0 auto;">
  <tr><td style="border-top:3px solid #1a0f06;border-bottom:1px solid #c5a882;padding:1.5rem 0;text-align:center;">
    <span style="font-family:monospace;font-size:0.55rem;letter-spacing:0.22em;text-transform:uppercase;color:#8b4513;display:block;margin-bottom:0.4rem;">Bienvenido</span>
    <span style="font-size:2.4rem;font-weight:900;color:#1a0f06;font-family:Georgia,serif;letter-spacing:-0.02em;">First Cup</span>
    <span style="display:block;font-family:monospace;font-size:0.52rem;letter-spacing:0.18em;text-transform:uppercase;color:#9a8572;margin-top:0.4rem;">IA · Desarrollo · Tecnología</span>
  </td></tr>
  <tr><td style="padding:2rem 0;">
    <p style="font-size:1.05rem;line-height:1.7;color:#4a3728;margin:0 0 1rem;">Ya eres parte de First Cup.</p>
    <p style="font-size:0.95rem;line-height:1.7;color:#4a3728;margin:0 0 1rem;">
      Cada mañana a las <strong>07:00</strong>, un agente analiza GitHub Trending, Hacker News, papers de IA
      y las mejores fuentes tech — y publica los 6 artículos más importantes del día en
      <a href="${site}" style="color:#8b4513;">${site}</a>.
    </p>
    <p style="font-size:0.9rem;line-height:1.7;color:#6b5744;margin:0 0 1.5rem;">
      Para recibir el digest directamente en tu inbox cada mañana (más alertas de breaking news
      y el resumen semanal del domingo), pásate al plan Premium.
    </p>
    <table cellpadding="0" cellspacing="0"><tr><td>
      <a href="${site}/subscribe" style="display:inline-block;background:#8b4513;color:#f5f0e8;
         text-decoration:none;font-family:monospace;font-size:0.7rem;font-weight:700;
         letter-spacing:0.14em;text-transform:uppercase;padding:0.75rem 1.75rem;">
        Ver plan Premium →
      </a>
    </td></tr></table>
  </td></tr>
  <tr><td style="border-top:1px solid #c5a882;padding:1rem 0;text-align:center;">
    <p style="font-family:monospace;font-size:0.58rem;color:#9a8572;margin:0;">
      © 2026 First Cup · <a href="${site}" style="color:#8b4513;text-decoration:none;">first-cup.es</a>
    </p>
  </td></tr>
</table></td></tr></table>
</body></html>`;
}
