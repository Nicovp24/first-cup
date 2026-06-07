import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  site: 'https://first-cup.es',
  output: 'hybrid',
  adapter: vercel(),
  integrations: [mdx()],
});
