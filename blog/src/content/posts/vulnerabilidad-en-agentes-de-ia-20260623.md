---
title: "Vulnerabilidad en agentes de IA"
date: "2026-06-23"
description: "Un ataque de 'agent jacking' puede comprometer la seguridad de agentes de inteligencia artificial como Claude Code, Cursor y Codex con solo una clave pública de Sentry."
tags: ["IA", "seguridad", "Dev"]
cover: "https://images.unsplash.com/photo-1555949963-aa79dcee981c?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/agentjacking-sentry-mcp-attack/"
---

Un ataque de "agent jacking" puede comprometer la seguridad de agentes de inteligencia artificial como Claude Code, Cursor y Codex con solo una clave pública de Sentry. El equipo de Threat Labs de Tenet Security, una startup de seguridad de agentes de inteligencia artificial que acaba de salir de la clandestinidad, documentó este problema el 17 de junio. La vulnerabilidad se describe en un [artículo](https://thenewstack.io/agentjacking-sentry-mcp-attack/) publicado en The New Stack, que destaca la importancia de la seguridad en el desarrollo de agentes de inteligencia artificial. La noticia llega en un momento en que la industria de la inteligencia artificial está experimentando un crecimiento rápido y la seguridad se convierte en una preocupación cada vez más importante.

## Qué es / Qué ha pasado
El ataque de "agent jacking" se basa en la explotación de una vulnerabilidad en el protocolo de contexto de modelo (MCP) que permite a los atacantes tomar el control de los agentes de inteligencia artificial. La clave pública de Sentry es el punto de entrada para este ataque, lo que significa que cualquier agente que utilice esta clave puede ser vulnerable. Los agentes afectados incluyen Claude Code, Cursor y Codex, que son herramientas de desarrollo de inteligencia artificial utilizadas para crear modelos de lenguaje y otros modelos de aprendizaje automático. La vulnerabilidad se debe a la falta de autenticación y autorización en el protocolo MCP, lo que permite a los atacantes enviar comandos maliciosos a los agentes.

## Por qué importa ahora
La seguridad de los agentes de inteligencia artificial es un tema cada vez más importante en la industria de la tecnología. A medida que los modelos de inteligencia artificial se vuelven más avanzados y se utilizan en una variedad de aplicaciones, la posibilidad de que sean utilizados para fines maliciosos aumenta. La vulnerabilidad descubierta por el equipo de Threat Labs de Tenet Security destaca la necesidad de una seguridad más robusta en el desarrollo de agentes de inteligencia artificial. La industria de la inteligencia artificial ha estado experimentando un crecimiento rápido en los últimos años, y la seguridad se convierte en una preocupación cada vez más importante. La noticia de esta vulnerabilidad puede llevar a los desarrolladores a reevaluar sus enfoques de seguridad y a considerar la implementación de medidas de seguridad más robustas.

## Detalles técnicos y qué significa para ti
El ataque de "agent jacking" se basa en la explotación de la vulnerabilidad en el protocolo MCP, que permite a los atacantes enviar comandos maliciosos a los agentes. La clave pública de Sentry es el punto de entrada para este ataque, lo que significa que cualquier agente que utilice esta clave puede ser vulnerable. 
```python
# Ejemplo de código vulnerable
import sentry_sdk

sentry_sdk.init(
    dsn="https://public_key@sentry.io/project_id",
    traces_sample_rate=1.0
)
```
> "La vulnerabilidad se debe a la falta de autenticación y autorización en el protocolo MCP, lo que permite a los atacantes enviar comandos maliciosos a los agentes." - Tenet Security. La implicación práctica de esta vulnerabilidad es que los desarrolladores deben reconsiderar su enfoque de seguridad y considerar la implementación de medidas de seguridad más robustas, como la autenticación y autorización en el protocolo MCP.

**Bottom line:** La seguridad de los agentes de inteligencia artificial es un tema cada vez más importante en la industria de la tecnología, y la vulnerabilidad descubierta por el equipo de Threat Labs de Tenet Security destaca la necesidad de una seguridad más robusta en el desarrollo de agentes de inteligencia artificial.

**Ver también:** [A public Sentry key is all it takes to hijack Claude Code, Cursor, and Codex](https://thenewstack.io/agentjacking-sentry-mcp-attack/) · [Documentación de Sentry](https://docs.sentry.io/)
