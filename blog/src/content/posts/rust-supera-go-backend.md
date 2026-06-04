---
title: "Rust supera a Go en adopción de nuevos proyectos backend por tercer año consecutivo"
date: "2026-05-28"
description: "El informe anual de Stack Overflow confirma que Rust lidera la adopción en proyectos backend nuevos, con un 34% de los encuestados usándolo en producción — frente al 28% de Go y el 21% de TypeScript/Node."
tags: ["Dev", "Rust", "tendencias"]
cover: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=75"
source_urls:
  - "https://stackoverflow.blog"
  - "https://news.ycombinator.com"
  - "https://crates.io"
---

## Los números

La encuesta anual de Stack Overflow 2026 (90.000 desarrolladores) revela un cambio de tendencia sostenido:

| Lenguaje | Uso en producción (backend) | Cambio vs 2025 |
|---|---|---|
| Rust | 34% | +8pp |
| Go | 28% | +2pp |
| TypeScript/Node | 21% | -3pp |
| Python (FastAPI/Django) | 18% | -1pp |

## Por qué está pasando

Tres factores explican la aceleración de Rust en producción:

**Tokio estabilizado.** El ecosistema async de Rust ha madurado. Tokio 2.0 simplificó la API y redujo la curva de aprendizaje para equipos que vienen de Go o Node.

**Compilación cruzada a WASM.** Rust es el lenguaje de facto para módulos WebAssembly en edge computing. Con Cloudflare Workers y Fastly Compute adoptando WASM como primera clase, la demanda se disparó.

**Memoria sin GC en sistemas críticos.** En servicios que procesan millones de eventos/segundo — motores de recomendación, trading, inference servers — el control fino sobre memoria compensa la curva de aprendizaje.

## El elefante en la habitación

El tiempo de compilación sigue siendo el principal pain point (64% de los encuestados). Incremental compilation en cargo mejoró, pero proyectos grandes todavía superan los 2 minutos en builds limpios.

---

**Bottom line:** Si arrancas un proyecto backend nuevo hoy y el equipo tiene 6+ meses, la apuesta por Rust tiene sentido. Para prototipos rápidos y equipos pequeños, Go sigue siendo la opción más pragmática.
