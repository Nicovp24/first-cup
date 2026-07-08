---
title: "SkyPilot y Hugging Face integrados"
date: "2026-07-08"
description: "La integración de SkyPilot con Hugging Face permite ejecutar cargas de trabajo de inteligencia artificial en cualquier nube y almacenar resultados sin costos de egreso."
tags: ["IA", "herramientas", "open-source"]
cover: "https://huggingface.co/blog/assets/skypilot-hf-storage/thumbnail.png"
source_urls:
  - "https://huggingface.co/blog/skypilot-hf-storage"
---

Hugging Face ha anunciado la integración de SkyPilot con su plataforma, lo que permite a los usuarios ejecutar cargas de trabajo de inteligencia artificial en cualquier nube y almacenar los resultados en Hugging Face sin incurrir en costos de egreso. Esta funcionalidad se presenta en un momento en que la demanda de soluciones de almacenamiento y procesamiento de datos en la nube es cada vez mayor. La noticia puede encontrarse en el [blog de Hugging Face](https://huggingface.co/blog/skypilot-hf-storage), donde se detallan las características y beneficios de esta integración.

## Qué es / Qué ha pasado
La plataforma de Hugging Face es conocida por su modelo de código abierto y su comunidad activa, con más de 100.000 modelos de lenguaje y más de 10.000 contribuyentes. La integración con SkyPilot permite a los usuarios aprovechar la escalabilidad y flexibilidad de la nube para ejecutar sus cargas de trabajo de inteligencia artificial, y luego almacenar los resultados en Hugging Face sin tener que preocuparse por los costos de transferencia de datos. Esto es especialmente útil para proyectos que requieren grandes cantidades de datos y cálculos intensivos, como el ajuste fino de modelos de lenguaje o la inferencia en grandes conjuntos de datos.

## Por qué importa ahora
La capacidad de ejecutar cargas de trabajo de inteligencia artificial en cualquier nube y almacenar los resultados en una plataforma centralizada como Hugging Face es crucial en la actualidad, ya que la cantidad de datos y la complejidad de los modelos de inteligencia artificial están aumentando rápidamente. La tendencia hacia la computación en la nube y el almacenamiento de datos en la nube ha llevado a una mayor demanda de soluciones que puedan manejar estas cargas de trabajo de manera eficiente y escalable. La integración de SkyPilot con Hugging Face refuerza esta tendencia y proporciona una solución más completa para los usuarios de inteligencia artificial.

## Detalles técnicos y qué significa para ti
La arquitectura de SkyPilot se basa en un modelo de contenedores que permite a los usuarios ejecutar sus cargas de trabajo de inteligencia artificial en cualquier nube, sin necesidad de modificar su código. La integración con Hugging Face se logra a través de una API que permite a los usuarios almacenar y recuperar sus modelos y datos de manera segura y eficiente. 
```python
import huggingface_hub
from huggingface_hub import Repository

# Inicializar el repositorio de Hugging Face
repo = Repository(
    local_dir="./my_model",
    repo_id="username/my_model",
    repo_type="model",
)

# Subir el modelo a Hugging Face
repo.push_to_hub(commit_message="Nuevo modelo de lenguaje")
```
> "Con SkyPilot, los usuarios pueden ejecutar cargas de trabajo de inteligencia artificial en cualquier nube y almacenar los resultados en Hugging Face sin incurrir en costos de egreso, lo que reduce significativamente los costos y la complejidad de la infraestructura", según el equipo de Hugging Face.
La integración de SkyPilot con Hugging Face es especialmente útil para proyectos que requieren una gran cantidad de datos y cálculos intensivos, como el ajuste fino de modelos de lenguaje o la inferencia en grandes conjuntos de datos.

**Bottom line:** La integración de SkyPilot con Hugging Face permite a los usuarios ejecutar cargas de trabajo de inteligencia artificial en cualquier nube y almacenar los resultados en Hugging Face sin incurrir en costos de egreso, lo que reduce significativamente los costos y la complejidad de la infraestructura.
**Ver también:** [SkyPilot y Hugging Face](https://huggingface.co/blog/skypilot-hf-storage) · [Documentación de Hugging Face](https://huggingface.co/docs)
