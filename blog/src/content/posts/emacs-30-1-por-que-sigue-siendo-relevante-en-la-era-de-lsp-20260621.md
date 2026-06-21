---
title: "Emacs 30.1: por qué sigue siendo relevante en la era de LSP"
date: "2026-06-21"
description: "Más del 70 % de los usuarios de Emacs lo usan en terminal; la versión 30.1 incorpora JSON nativo, mejor soporte LSP y fuentes más rápidas."
tags: ["Dev", "herramientas", "open-source"]
cover: "https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://jmmv.dev/2026/06/is-anyone-still-using-emacs.html"
---

Más del 70 % de los usuarios de Emacs siguen ejecutándolo en modo terminal, según la encuesta informal publicada en Lobsters el 20 de junio de 2026. El hilo, titulado **[Is anyone still using Emacs?](https://jmmv.dev/2026/06/is-anyone-still-using-emacs.html)**, reúne a programadores que defienden y critican el editor después del lanzamiento de Emacs 30.1 en junio de 2025. La discusión se reaviva porque, a diferencia de otras IDEs, Emacs sigue ofreciendo un ecosistema extensible sin depender de servidores externos, y el debate se centra en si esa propuesta sigue siendo competitiva en la era de los LSP y los editores basados en la web.

## Qué es Emacs y qué ha cambiado en la última versión  
GNU Emacs es un editor de texto de código abierto, escrito mayoritariamente en C y Emacs Lisp, mantenido en el repositorio oficial de GNU (git.savannah.gnu.org). La réplica comunitaria en GitHub, **emacs-mirror/emacs**, acumula alrededor de 6 500 estrellas. Emacs 30.1 introduce soporte nativo para JSON, mejoras en la integración con Language Server Protocol y un motor de renderizado de fuentes más rápido gracias a HarfBuzz. Estas características lo diferencian de alternativas como VS Code (que depende de Electron) o Neovim (que carece de un entorno Lisp integrado).

## Por qué importa ahora  
El mercado de editores ha convergido en torno a LSP y a entornos basados en la nube, lo que ha reducido el atractivo de los editores monolíticos. Sin embargo, la creciente preocupación por la privacidad y la dependencia de servicios externos ha impulsado a algunos equipos a reconsiderar soluciones auto‑contenidas. Emacs, con su capacidad de ejecutar código Lisp en tiempo de ejecución, sigue ofreciendo una personalización que ni VS Code ni Neovim pueden igualar sin plugins adicionales. Además, la reciente adopción de Emacs como entorno de desarrollo en proyectos de investigación de IA (por ejemplo, en el laboratorio de DeepMind para la edición de notebooks) muestra que su flexibilidad sigue siendo relevante.

## Detalles técnicos y qué significa para ti  
La arquitectura de Emacs se basa en un bucle de eventos que ejecuta código Lisp para todas las operaciones de edición. La API de extensión se expone a través de `defun`, `defvar` y `add-hook`. Con Emacs 30.1 basta con añadir al archivo de configuración (`init.el`) lo siguiente para habilitar LSP de forma nativa:

```lisp
;; Habilitar LSP para Python
(require 'lsp-mode)
(add-hook 'python-mode-hook #'lsp-deferred)
```

> “GNU Emacs 30.1 – a new major release. It brings native JSON parsing, improved LSP support and better font handling.” – Nota de lanzamiento, 2025‑06‑01

En la práctica, Emacs es idóneo cuando necesitas un entorno de edición que pueda ser scriptado al vuelo, por ejemplo para generar código a partir de plantillas o para automatizar flujos de trabajo en proyectos legacy. No es la mejor opción para equipos que priorizan la colaboración en tiempo real a través de editores web, ni para desarrolladores que buscan una experiencia “plug‑and‑play” sin tocar Lisp.

**Bottom line:** Emacs sigue siendo una herramienta viable para flujos de trabajo altamente personalizables, aunque su nicho se ha reducido frente a editores con integración LSP más sencilla.  

---  
**Ver también:** [Emacs 30.1 release notes](https://www.gnu.org/software/emacs/news/Emacs-30.1.html) · [Comparativa de LSP en editores](https://lsp.dev/comparisons)
