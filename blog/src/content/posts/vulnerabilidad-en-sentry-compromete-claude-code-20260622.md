---
title: "Vulnerabilidad en Sentry compromete Claude Code"
date: "2026-06-22"
description: "Una clave pública de Sentry es suficiente para tomar el control de Claude Code, Cursor y Codex, lo que pone en riesgo la seguridad de la inteligencia artificial."
tags: ["IA", "seguridad", "herramientas"]
cover: "https://images.unsplash.com/photo-1555949963-aa79dcee981c?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/agentjacking-sentry-mcp-attack/"
---

Una clave pública de Sentry es todo lo que se necesita para comprometer Claude Code, Cursor y Codex, según un informe publicado por el equipo Threat Labs de Tenet Security el 17 de junio. Esto ha generado una gran preocupación en la comunidad de seguridad de la inteligencia artificial, ya que estas herramientas son ampliamente utilizadas en el desarrollo de modelos de lenguaje y otros proyectos de IA. Puedes leer más sobre este incidente en [A public Sentry key is all it takes to hijack Claude Code, Cursor, and Codex](https://thenewstack.io/agentjacking-sentry-mcp-attack/).

## Qué es / Qué ha pasado
El equipo Threat Labs de Tenet Security, una startup de seguridad de agentes de inteligencia artificial que recientemente salió de la clandestinidad, documentó una vulnerabilidad en el protocolo de contexto de modelo (MCP) que permite a un atacante tomar el control de Claude Code, Cursor y Codex utilizando solo una clave pública de Sentry. Esto es especialmente preocupante, ya que estas herramientas son utilizadas por muchos desarrolladores y empresas para crear y entrenar modelos de lenguaje y otros proyectos de IA. El protocolo MCP es un estándar para la comunicación entre agentes de inteligencia artificial y los modelos que utilizan, por lo que una vulnerabilidad en este protocolo puede tener consecuencias graves.

## Por qué importa ahora
La seguridad de la inteligencia artificial es un tema que ha estado ganando importancia en los últimos años, ya que los modelos de lenguaje y otros proyectos de IA se están volviendo cada vez más comunes en la industria. La vulnerabilidad descubierta por el equipo Threat Labs de Tenet Security destaca la importancia de la seguridad en la inteligencia artificial y la necesidad de proteger las claves públicas de Sentry y otros secretos de autenticación. La comunidad de inteligencia artificial ha estado trabajando en la creación de estándares y protocolos de seguridad para proteger los modelos y los datos, pero este incidente muestra que todavía hay mucho trabajo por hacer. La tendencia hacia la adopción de la inteligencia artificial en la industria refuerza la importancia de esta noticia, ya que las empresas y los desarrolladores deben tomar medidas para proteger sus modelos y datos.

## Detalles técnicos y qué significa para ti
La vulnerabilidad descubierta por el equipo Threat Labs de Tenet Security se debe a una debilidad en el protocolo MCP que permite a un atacante autenticarse como un agente de inteligencia artificial legítimo utilizando solo una clave pública de Sentry. Esto significa que un atacante puede tomar el control de Claude Code, Cursor y Codex, y utilizarlos para realizar acciones maliciosas. 
```python
# Ejemplo de cómo un atacante podría autenticarse como un agente de inteligencia artificial legítimo
import requests

sentry_key = "clave_pública_de_sentry"
url = "https://example.com/mcp"

response = requests.post(url, headers={"Authorization": f"Bearer {sentry_key}"})

if response.status_code == 200:
    print("Autenticación exitosa")
else:
    print("Autenticación fallida")
```
> "La vulnerabilidad en el protocolo MCP es un recordatorio de que la seguridad de la inteligencia artificial es un tema crítico que requiere atención inmediata", según el informe del equipo Threat Labs de Tenet Security.

## Cierre
**Bottom line:** La vulnerabilidad descubierta por el equipo Threat Labs de Tenet Security destaca la importancia de la seguridad en la inteligencia artificial y la necesidad de proteger las claves públicas de Sentry y otros secretos de autenticación.

**Ver también:** [A public Sentry key is all it takes to hijack Claude Code, Cursor, and Codex](https://thenewstack.io/agentjacking-sentry-mcp-attack/) · [Tenet Security](https://tenetsecurity.io/)
