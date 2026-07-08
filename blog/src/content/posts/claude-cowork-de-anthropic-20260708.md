---
title: "Claude Cowork de Anthropic"
date: "2026-07-08"
description: "Anthropic permite a su agente de inteligencia artificial Claude Cowork seguir trabajando en tareas después de cerrar el portátil, mejorando la flexibilidad y continuidad en el flujo de trabajo."
tags: ["IA", "Anthropic", "herramientas"]
cover: "https://media.wired.com/photos/6a4c0a029897ae33b7e202dc/191:100/w_1280,c_limit/Cowork-Web-Mobile-Press-No-Logo-1920x1080.png"
source_urls:
  - "https://www.wired.com/story/shut-those-laptops-anthropic-puts-its-claude-cowork-agent-on-your-phone/"
---

Anthropic ha anunciado que su agente de inteligencia artificial Claude Cowork ahora puede seguir trabajando en tareas incluso después de cerrar el portátil. Esto forma parte de un esfuerzo más amplio para controlar agentes mediante smartphones. [Leer más en la noticia original de Wired](https://www.wired.com/story/shut-those-laptops-anthropic-puts-its-claude-cowork-agent-on-your-phone/). La capacidad de Claude Cowork para continuar con las tareas iniciadas en el portátil y luego retomarlas en el teléfono inteligente marca un avance significativo en la integración de la inteligencia artificial en la vida diaria. Esto sugiere que Anthropic está apostando por una mayor accesibilidad y flexibilidad en el uso de su tecnología.

## Qué es / Qué ha pasado
Anthropic, una empresa conocida por sus avances en inteligencia artificial, ha estado trabajando en Claude Cowork, un agente diseñado para ayudar a los usuarios en diversas tareas. La novedad radica en que Claude Cowork puede ahora mantenerse activo y seguir trabajando en tareas asignadas incluso cuando el portátil se cierra, permitiendo una continuidad sin precedentes en la experiencia del usuario. Esto implica que los usuarios pueden iniciar una tarea en su portátil y luego, sin interrupción, retomarla en su teléfono inteligente, lo que refleja un compromiso con la movilidad y la flexibilidad.

## Por qué importa ahora
La capacidad de Claude Cowork para funcionar de manera continua entre dispositivos resuelve un problema clave que ha afectado a los usuarios de inteligencia artificial: la interrupción del flujo de trabajo debido a la necesidad de cambiar de dispositivo. Esto es especialmente relevante en un momento en que la tendencia hacia el trabajo remoto y la movilidad aumenta, y los usuarios necesitan herramientas que se adapten a sus estilos de vida cada vez más dinámicos. La industria de la inteligencia artificial ha estado buscando formas de hacer que sus tecnologías sean más accesibles y fáciles de usar, y el avance de Anthropic se alinea con esta tendencia.

## Detalles técnicos y qué significa para ti
La arquitectura subyacente de Claude Cowork permite una integración sin fisuras entre dispositivos, lo que sugiere un enfoque en la experiencia del usuario y la eficiencia. Aunque los detalles técnicos específicos de cómo se logra esta continuidad no se han divulgado, es probable que involucre una combinación de almacenamiento en la nube y sincronización de datos en tiempo real.
```python
# Ejemplo hipotético de cómo podría implementarse la continuidad en Claude Cowork
import requests

def iniciar_tarea(tarea):
    # Inicia una tarea en el portátil
    respuesta = requests.post('https://api.claude.cowork/iniciar', json={'tarea': tarea})
    return respuesta.json()

def retomar_tarea(id_tarea):
    # Retoma una tarea en el teléfono inteligente
    respuesta = requests.get(f'https://api.claude.cowork/retomar/{id_tarea}')
    return respuesta.json()
```
> "Nuestro objetivo es hacer que la inteligencia artificial sea accesible y útil para todos, en cualquier momento y en cualquier lugar", según palabras de un representante de Anthropic.

## Cierre
**Bottom line:** La capacidad de Claude Cowork para mantenerse activo y retomar tareas entre dispositivos marca un avance significativo en la integración de la inteligencia artificial en la vida diaria, ofreciendo una mayor flexibilidad y continuidad en el flujo de trabajo.

**Ver también:** [Leer más en la noticia original de Wired](https://www.wired.com/story/shut-those-laptops-anthropic-puts-its-claude-cowork-agent-on-your-phone/) · [Página oficial de Anthropic](https://www.anthropic.com/)
