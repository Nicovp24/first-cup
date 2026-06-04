import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const posts = await getCollection('posts');
  const sorted = posts.sort((a, b) => b.data.date.valueOf() - a.data.date.valueOf());

  return rss({
    title: 'First Cup — IA, Dev & Tech',
    description: 'Tu café tech de cada mañana. IA, desarrollo y tecnología.',
    site: context.site!,
    items: sorted.map((post) => ({
      title: post.data.title,
      pubDate: post.data.date,
      description: post.data.description,
      link: `/${post.slug}/`,
      categories: post.data.tags,
    })),
    customData: `<language>es-ES</language>`,
  });
}
