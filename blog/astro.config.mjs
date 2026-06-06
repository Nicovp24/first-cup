import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import vercel from '@astrojs/vercel/serverless';

export default defineConfig({
  site: 'https://first-cup-kappa.vercel.app',
  output: 'hybrid',
  adapter: vercel(),
  integrations: [mdx()],
});
