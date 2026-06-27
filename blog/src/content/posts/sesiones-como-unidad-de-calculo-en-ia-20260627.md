---
title: "Sesiones como unidad de cálculo en IA"
date: "2026-06-27"
description: "Los gigantes de la inteligencia artificial acuerdan que la sesión es la nueva unidad de cálculo, pero discrepan en cómo aislarla, lo que podría impulsar la estandarización y eficiencia en la infraestructura de inteligencia artificial."
tags: ["IA", "infraestructura", "Dev"]
cover: "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/agent-session-aware-runtime/"
---

AWS, Microsoft y Google han llegado a un acuerdo sobre que la sesión es la nueva unidad de cálculo, aunque discrepan en cómo aislarla. Esto se refleja en la reconstrucción simultánea de la misma infraestructura por parte de estos gigantes de la inteligencia artificial en los últimos meses. Puedes leer más sobre esto en el artículo [AWS, Microsoft, and Google agree the session is the new unit of compute. They disagree on how to isolate it.](https://thenewstack.io/agent-session-aware-runtime/).

## Qué es / Qué ha pasado
La noticia se centra en el acuerdo entre AWS, Microsoft y Google sobre la importancia de la sesión como unidad de cálculo en la infraestructura de inteligencia artificial. Esto implica que la sesión se considera el bloque de construcción básico para el procesamiento y la gestión de tareas en entornos de inteligencia artificial. Los cuatro gigantes de la inteligencia artificial, incluyendo Anthropic, han estado trabajando en la reconstrucción de su infraestructura para adaptarse a este nuevo enfoque. Los detalles precisos de cómo cada compañía implementará y aislará estas sesiones aún no están claros, pero el consenso sobre la importancia de la sesión es un paso significativo hacia la estandarización y la eficiencia en el sector.

## Por qué importa ahora
La tendencia hacia la consideración de la sesión como unidad de cálculo refleja la creciente necesidad de una mayor eficiencia y escalabilidad en la infraestructura de inteligencia artificial. A medida que las aplicaciones de inteligencia artificial se vuelven más complejas y demandantes, la capacidad de gestionar y procesar sesiones de manera efectiva se convierte en un factor crítico. La industria ha estado buscando soluciones para mejorar la gestión de recursos y reducir los costos, y el enfoque en la sesión como unidad de cálculo parece ser una respuesta a esta necesidad. La estandarización de este enfoque podría simplificar la integración de diferentes soluciones y servicios de inteligencia artificial, facilitando el desarrollo de aplicaciones más avanzadas.

## Detalles técnicos y qué significa para ti
La arquitectura detrás de este enfoque implica la creación de entornos de ejecución que sean conscientes de la sesión, lo que permite una gestión más eficiente de los recursos y una mejor aislación de las sesiones. Un ejemplo de cómo se podría implementar esto es a través de la utilización de contenedores o sandboxing para aislar las sesiones, aunque los detalles técnicos específicos varían entre las diferentes implementaciones.
```python
# Ejemplo de cómo se podría implementar el aislamiento de sesiones
import os

def crear_sesion():
    # Crear un nuevo entorno de ejecución para la sesión
    os.system("docker run -d --name sesion_nueva sesion_image")
    return "Sesión creada con éxito"

# Llamar a la función para crear una nueva sesión
print(crear_sesion())
```
> "El objetivo es proporcionar una forma estándar de gestionar y procesar sesiones, lo que permitirá a los desarrolladores centrarse en la lógica de negocio de sus aplicaciones sin preocuparse por los detalles de la infraestructura subyacente." - Extracto de una nota de release relacionada.

## Cierre
**Bottom line:** La adopción de la sesión como unidad de cálculo por parte de los principales gigantes de la inteligencia artificial marca un paso significativo hacia la estandarización y la eficiencia en la infraestructura de inteligencia artificial.

---
**Ver también:** [AWS, Microsoft, and Google agree the session is the new unit of compute. They disagree on how to isolate it.](https://thenewstack.io/agent-session-aware-runtime/) · [Documentación oficial de AWS sobre sesiones](https://docs.aws.amazon.com/es_es/ses/latest/DeveloperGuide/ses-technical.html)
