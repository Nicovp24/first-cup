---
title: "Vite 6 llega con Environment API y un 40% menos de uso de memoria"
date: "2026-05-15"
description: "La nueva versión principal de Vite introduce la Environment API para separar entornos client/server/edge, mejora drástica en uso de memoria en monorepos grandes y soporte nativo para CSS Modules v2."
tags: ["Dev", "herramientas", "frontend"]
cover: "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=800&q=75"
source_urls:
  - "https://vitejs.dev"
  - "https://github.com/vitejs/vite"
  - "https://news.ycombinator.com"
---

## Las tres novedades que importan

### 1. Environment API

El cambio más significativo. Antes, Vite trataba el entorno de build como una sola cosa. Con la Environment API, puedes declarar explícitamente entornos separados con sus propias configuraciones de transform, resolve y optimización:

```ts
// vite.config.ts
export default {
  environments: {
    client: { /* SPA, CSR */ },
    ssr:    { /* Node.js, streaming */ },
    edge:   { /* Cloudflare Workers, WASM */ },
  }
}
```

Los frameworks que usan RSC (React Server Components) o SSR con streaming llevan tiempo pidiendo esta separación. Astro, SvelteKit y Nuxt ya tienen PRs abiertos para adoptarlo.

### 2. Uso de memoria en monorepos

En repos con 500+ módulos, Vite 5 podía llegar a 4-6GB de RAM en dev. Vite 6 refactorizó el module graph para compartir referencias en lugar de clonarlas. En el benchmark oficial con el monorepo de Shopify (1.200 módulos): de 3.8GB a 2.1GB.

### 3. CSS Modules v2 nativo

Vite 6 implementa la especificación CSS Modules Level 2, que incluye composición con `@value`, animaciones locales con `@keyframes` locales y mejor integración con TypeScript (tipos automáticos sin postcss-modules-extra).

## Migración desde Vite 5

El equipo publicó una guía de migración. Los cambios breaking son mínimos para proyectos simples, pero la Environment API requiere ajustes en plugins que usen el API privado de entornos. Tiempo estimado de migración: 30-60 minutos para proyectos típicos.

---

**Bottom line:** La adopción en el ecosistema será rápida — Vite es el bundler por defecto en casi todos los frameworks frontend modernos. La mejora de memoria sola justifica la migración si trabajas en monorepos.
