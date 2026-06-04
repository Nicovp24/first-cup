// Vercel serverless function: POST /api/subscribe
// Saves email to Supabase subscribers table.

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, message: 'Method not allowed' });
  }

  const email = typeof req.body?.email === 'string' ? req.body.email.trim() : '';

  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ ok: false, message: 'Email inválido.' });
  }

  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.error('[subscribe] Missing Supabase env vars');
    return res.status(500).json({ ok: false, message: 'Error de configuración.' });
  }

  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/subscribers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Prefer': 'return=minimal',
      },
      body: JSON.stringify({ email }),
    });

    // 409 = email already exists (unique constraint) — treat as success
    if (response.ok || response.status === 409) {
      return res.status(200).json({ ok: true, message: '¡Apuntado! Te avisamos cuando salga cada edición.' });
    }

    const error = await response.text();
    console.error('[subscribe] Supabase error:', response.status, error);
    return res.status(500).json({ ok: false, message: 'Error al guardar tu email.' });

  } catch (err) {
    console.error('[subscribe] fetch error:', err);
    return res.status(500).json({ ok: false, message: 'Error interno del servidor.' });
  }
}
