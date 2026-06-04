import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://nexusdigest.com',
  output: 'hybrid',
  integrations: [mdx(), sitemap()],
});
