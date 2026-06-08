import { getCollection } from 'astro:content';
import type { APIRoute } from 'astro';

export const GET: APIRoute = async ({ site }) => {
  const posts = await getCollection('posts');
  const base = site?.toString().replace(/\/$/, '') ?? 'https://first-cup.es';

  // Static pages
  const staticPages = [
    { path: '',            priority: '1.0', changefreq: 'daily'   },
    { path: '/subscribe',  priority: '0.8', changefreq: 'monthly' },
    { path: '/cuenta',     priority: '0.5', changefreq: 'monthly' },
  ].map(({ path, priority, changefreq }) => `
  <url>
    <loc>${base}${path}/</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`);

  // Individual posts
  const postPages = posts.map(post => `
  <url>
    <loc>${base}/${post.slug}/</loc>
    <lastmod>${post.data.date.toISOString().split('T')[0]}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>`);

  // Edition pages — one URL per unique edition number derived from post dates
  const editionDates = [...new Set(
    posts.map(p => p.data.date.toISOString().split('T')[0])
  )].sort();
  const editionPages = editionDates.map((date, i) => `
  <url>
    <loc>${base}/edicion/${i + 1}/</loc>
    <lastmod>${date}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>`);

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${[...staticPages, ...postPages, ...editionPages].join('')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml' },
  });
};
