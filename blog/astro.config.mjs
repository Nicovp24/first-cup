import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import vercel from '@astrojs/vercel';

export default defineConfig({
  site: 'https://firstcup.dev',
  output: 'hybrid',
  adapter: vercel(),
  integrations: [mdx()],
});
