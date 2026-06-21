---
title: "Google retira Gemini CLI y la comunidad pasa a Antigravity"
date: "2026-06-21"
description: "Google retira el Gemini CLI, cliente de línea de comandos; la comunidad lo sustituye con Antigravity, y los equipos deben usar los SDK de Google Cloud."
tags: ["IA", "herramientas", "Rust", "open-source"]
cover: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/gemini-cli-antigravity-replacement/"
---

Google ha retirado el Gemini CLI, su herramienta de línea de comandos para los modelos Gemini, tras menos de un año de vida. El anuncio, publicado en *The New Stack* (<https://thenewstack.io/gemini-cli-antigravity-replacement/>), llega cuando la comunidad ya está probando alternativas como Antigravity para cubrir el vacío dejado por Google.

## Qué es Gemini CLI y qué ha ocurrido  
El repositorio oficial era **google/gemini-cli**, escrito en Python y distribuido como paquete `pip`. En el momento del cierre acumulaba **más de 100 000 estrellas en GitHub**, lo que lo convirtió rápidamente en el cliente de IA de línea de comandos más popular de Google. Su objetivo era ofrecer una forma directa de invocar los modelos Gemini desde el terminal, sin necesidad de escribir código cliente: basta con `gemini chat "¿Cuál es la diferencia entre un LLM y un agente?"`.  

A diferencia de la CLI de OpenAI, que depende de la API pública de OpenAI, Gemini CLI estaba ligada a la infraestructura de Google Cloud y gestionaba la autenticación mediante credenciales de `gcloud`. La herramienta competía con proyectos como **Antigravity** (un cliente de código abierto basado en Rust) y con los SDK genéricos de Google Cloud que, aunque completos, requieren más configuración para tareas de prueba rápida.

La decisión de descontinuar el proyecto se anunció en el mismo repositorio con una nota de release que indica que el mantenimiento pasará a la documentación oficial y a los SDK de Cloud. El código seguirá disponible bajo la licencia Apache 2.0, pero no recibirá actualizaciones ni parches de seguridad.

## Por qué importa ahora  
El mercado de agentes de IA ha explotado en los últimos meses: startups lanzan bots de asistencia, los equipos de DevOps automatizan flujos con LLMs y los investigadores usan prompts para validar hipótesis. En este contexto, la ausencia de una CLI oficial de Google crea una brecha de productividad.  

Antigravity surgió como respuesta comunitaria, ofreciendo una interfaz mínima que envía peticiones HTTP a la API de Gemini. Aunque carece del soporte de Google, su arquitectura ligera y su compilación en Rust le otorgan velocidad y portabilidad. La retirada del Gemini CLI refuerza la tendencia de que los proveedores de IA deleguen la mayor parte del tooling a la comunidad, mientras enfocan sus recursos en mejoras del modelo y en la integración con plataformas de nube.

Además, la noticia coincide con el lanzamiento de **Gemini 1.5**, la última generación de modelos de Google, que se promociona como “listo para producción”. Sin una CLI oficial, los equipos tendrán que adaptar sus pipelines a los SDK de Cloud o a clientes de terceros, lo que puede introducir fricciones en entornos donde la velocidad de iteración es crítica.

## Detalles técnicos y qué significa para ti  
Gemini CLI se construía sobre una capa de gRPC que empaquetaba las peticiones en JSON y gestionaba la autenticación mediante el token de acceso de `gcloud`. El proceso de instalación era tan sencillo como:

```bash
pip install gemini-cli
gcloud auth login
gemini chat "Explica la arquitectura de Transformers"
```

El comando `gemini chat` iniciaba una sesión interactiva, mientras que `gemini complete` permitía generar texto a partir de un prompt único. El README destacaba la filosofía “zero‑config”:

> *“Gemini CLI provides a fast, zero‑config way to call Gemini models from your shell, leveraging your existing gcloud credentials.”*

Para los usuarios que dependían de la CLI para pruebas rápidas, la implicación inmediata es migrar a un cliente HTTP manual o adoptar Antigravity. La primera opción requiere escribir código de envoltorio (por ejemplo, con `requests` en Python) y gestionar manualmente la cuota y la paginación. Antigravity, por su parte, ofrece comandos equivalentes (`antigravity chat`) pero sin garantías de compatibilidad futura con cambios de la API de Gemini.

En la práctica, la CLI sigue siendo útil para prototipos y depuración en entornos locales, pero no es adecuada para pipelines de CI/CD ni para entornos de producción donde la estabilidad y el soporte oficial son obligatorios. En esos casos, los SDK de Google Cloud (por ejemplo, `google-cloud-aiplatform`) siguen siendo la opción recomendada.

## Alternativas y camino a seguir  
- **Antigravity** (github.com/antigravity/cli): cliente Rust, binario estático, sin dependencias de Python.  
- **Google Cloud SDK** (`gcloud ai models`): integración completa con IAM y facturación.  
- **Wrappers personalizados**: usar `curl` o bibliotecas como `requests` para interactuar directamente con la API de Gemini.  

La comunidad ya está creando forks de Gemini CLI que añaden soporte a Antigravity y a otros entornos, pero la falta de un mantenedor oficial implica que la calidad y la seguridad dependerán de contribuciones externas.

**Bottom line:** La retirada del Gemini CLI obliga a los equipos que usan modelos Gemini a migrar a soluciones menos integradas, lo que acelera la adopción de herramientas comunitarias como Antigravity y refuerza la dependencia de los SDK de Google Cloud para entornos de producción.  

**Ver también:** [Gemini CLI vs. Antigravity: What works, not the spec sheet](https://thenewstack.io/gemini-cli-antigravity-replacement/) · [Google Cloud AI Platform SDK](https://cloud.google.com/ai-platform)
