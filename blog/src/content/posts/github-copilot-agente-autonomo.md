---
title: "GitHub Copilot se convierte en agente: puede abrir PRs, pasar tests y deployar"
date: "2026-06-01"
description: "GitHub lanzó Copilot Agent Mode, que permite al asistente ejecutar ciclos completos de desarrollo: escribir código, ejecutar tests, iterar sobre errores y abrir pull requests sin intervención del desarrollador."
tags: ["Dev", "GitHub", "herramientas"]
cover: "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?auto=format&fit=crop&w=800&q=75"
source_urls:
  - "https://github.blog"
  - "https://news.ycombinator.com"
---

## Copilot Agent Mode: el ciclo completo

GitHub presentó en su conferencia Universe 2026 el modo agente de Copilot, un salto cualitativo respecto al autocompletado y el chat. El agente puede:

1. **Leer el contexto del repo** — entiende la arquitectura, tests existentes, guías de estilo y CI/CD.
2. **Implementar features completas** — dado un issue de GitHub, genera el código, lo prueba y lo itera.
3. **Pasar la CI** — ejecuta tests localmente, corrige fallos, repite hasta que pasa.
4. **Abrir un PR** — con título, descripción, etiquetas y reviewers asignados automáticamente.

En los demos, el agente completó features de complejidad media en 8-15 minutos de reloj.

## Límites actuales

El agente falla de forma predecible en dos escenarios: cambios que requieren decisiones de arquitectura no documentadas y features que tocan múltiples servicios con contratos implícitos entre equipos. GitHub reconoce esto y posiciona el agente como "pair programmer asincrónico", no como sustituto.

## Precio y disponibilidad

Incluido en Copilot Enterprise ($39/usuario/mes) a partir de julio. Copilot Business tendrá acceso en Q4 2026.

---

**Bottom line:** El modelo de "le asigno el issue y vuelvo a revisar el PR" empieza a ser viable para la mayoría de tareas CRUD y de refactoring. El stack de AI-assisted development acaba de subir otro peldaño.
