import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    date: z.coerce.date(),
    description: z.string(),
    tags: z.array(z.string()),
    source_urls: z.array(z.string().url()).optional(),
    cover: z.string().url().optional(),
  }),
});

export const collections = { posts };
