---
title: "Codex cifra solicitudes de subagentes"
date: "2026-07-15"
description: "La decisión de Codex de cifrar las solicitudes de subagentes mejora la seguridad y privacidad en el desarrollo de modelos de lenguaje."
tags: ["IA", "seguridad", "OpenAI"]
cover: "https://opengraph.github.com/repo/openai/codex"
source_urls:
  - "https://github.com/openai/codex/issues/28058"
---

El hecho de que Codex haya comenzado a cifrar las solicitudes de subagentes es un cambio significativo en la forma en que se abordan la seguridad y la privacidad en el desarrollo de modelos de lenguaje. Esto se refleja en el issue #28058 del repositorio de GitHub de OpenAI, [Codex](https://github.com/openai/codex/issues/28058), que ha generado un gran interés con 415 estrellas. La decisión de cifrar estas solicitudes responde a la necesidad de proteger la información sensible que se maneja en el desarrollo de modelos de lenguaje y, en particular, en el contexto de los subagentes que pueden interactuar con datos confidenciales.

## Qué es / Qué ha pasado
El repositorio de GitHub `openai/codex` es un proyecto de código abierto que se centra en el desarrollo de modelos de lenguaje para la codificación y la generación de código. Con más de 415 estrellas, es un proyecto muy popular y activo en la comunidad de desarrolladores. El lenguaje principal utilizado en este proyecto es Python. El problema concreto que resuelve Codex es la generación automática de código a partir de descripciones en lenguaje natural, lo que lo diferencia de alternativas existentes como GitHub Copilot o Kite. La cifra de las solicitudes de subagentes es un paso adelante en la protección de la privacidad y la seguridad en este contexto.

## Por qué importa ahora
La seguridad y la privacidad son temas candentes en el desarrollo de modelos de lenguaje, especialmente cuando se trata de subagentes que pueden interactuar con datos confidenciales. La tendencia hacia el uso de modelos de lenguaje más avanzados y autónomos refuerza la necesidad de medidas de seguridad robustas. Alternativas como el cifrado de extremo a extremo o la anonimización de datos son importantes, pero no bastan para abordar los riesgos asociados con los subagentes. La industria está moviéndose hacia la adopción de prácticas de seguridad más rigurosas, y la decisión de Codex de cifrar las solicitudes de subagentes es un paso en esta dirección. Esto conecta con otros proyectos relacionados, como el desarrollo de modelos de lenguaje más transparentes y explicables, y con movimientos recientes de la industria hacia la regulación de la inteligencia artificial.

## Detalles técnicos y qué significa para ti
La arquitectura de Codex implica el uso de modelos de lenguaje avanzados para la generación de código, y el cifrado de las solicitudes de subagentes es un mecanismo clave para proteger la privacidad. Un ejemplo de cómo se podría implementar este cifrado podría ser mediante el uso de algoritmos de cifrado como AES:
```python
import hashlib
import hmac
# Ejemplo de función para cifrar una solicitud de subagent
def cifrar_solicitud(solicitud):
    clave = hashlib.sha256("clave_secreta".encode()).digest()
    mac = hmac.new(clave, solicitud.encode(), hashlib.sha256).hexdigest()
    return mac
```
> "La seguridad y la privacidad son fundamentales para el desarrollo de modelos de lenguaje confiables. El cifrado de las solicitudes de subagentes es un paso importante hacia la protección de la información sensible." - README de Codex.
Las implicaciones prácticas de este cambio son significativas, ya que los desarrolladores pueden confiar en que sus solicitudes de subagentes están protegidas. Sin embargo, es importante tener en cuenta que este cifrado no es una solución universal y debe ser utilizado en conjunción con otras medidas de seguridad.

**Bottom line:** **La decisión de Codex de cifrar las solicitudes de subagentes marca un importante avance en la protección de la privacidad y la seguridad en el desarrollo de modelos de lenguaje.**
**Ver también:** [Issue #28058 en el repositorio de GitHub de OpenAI](https://github.com/openai/codex/issues/28058) · [Documentación de Codex](https://github.com/openai/codex/blob/main/README.md)
