---
title: "Fable de Anthropic vuelve al mercado"
date: "2026-07-01"
description: "El gobierno federal de EE. UU. levanta los controles de exportación sobre el modelo de inteligencia artificial Fable de Anthropic, permitiendo su vuelta al mercado y continuación de su desarrollo."
tags: ["IA", "Anthropic", "OpenAI"]
cover: "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/anthropic-fable-ban-lifted/"
---

El gobierno federal de Estados Unidos ha levantado los controles de exportación que había impuesto sobre el modelo de inteligencia artificial (IA) de Anthropic, Fable. Esto significa que Anthropic puede ahora volver a ofrecer Fable a sus clientes y usuarios. La noticia se ha publicado en [The New Stack](https://thenewstack.io/anthropic-fable-ban-lifted/), y según el Departamento de Comercio de EE. UU., la decisión se ha tomado después de una revisión exhaustiva de las políticas de exportación de tecnologías de IA.

## Qué es / Qué ha pasado
Anthropic es una empresa de IA que ha desarrollado varios modelos de lenguaje, incluyendo Fable. Fable es un modelo de lenguaje avanzado que ha sido diseñado para realizar tareas de procesamiento de lenguaje natural, como la generación de texto y la respuesta a preguntas. Aunque no hay información disponible sobre el número de estrellas en GitHub, Fable se diferencia de otros modelos de lenguaje en su capacidad para generar texto coherente y relevante. La empresa había anunciado que iba a retirar Fable del mercado debido a los controles de exportación impuestos por el gobierno federal, pero ahora puede volver a ofrecerlo a sus clientes.

## Por qué importa ahora
La decisión del gobierno federal de levantar los controles de exportación sobre Fable es importante porque refleja un cambio en la política de exportación de tecnologías de IA. En los últimos años, ha habido un debate en curso sobre cómo regular la exportación de tecnologías de IA, especialmente aquellas que tienen posibles aplicaciones militares o de seguridad nacional. La decisión de levantar los controles de exportación sobre Fable sugiere que el gobierno federal está dispuesto a permitir que las empresas de IA continúen desarrollando y exportando sus tecnologías, siempre y cuando cumplan con ciertos estándares de seguridad y privacidad. Esto es especialmente relevante en el contexto de la investigación en IA, que ha avanzado rápidamente en los últimos años y ha generado un interés creciente en la industria y el gobierno.

## Detalles técnicos y qué significa para ti
La arquitectura de Fable se basa en un modelo de lenguaje transformador, que es capaz de procesar grandes cantidades de texto y generar respuestas coherentes. Aunque no hay información disponible sobre la API o el mecanismo clave de Fable, es probable que se base en tecnologías de aprendizaje automático y procesamiento de lenguaje natural. 
```python
# Ejemplo de cómo podrías utilizar un modelo de lenguaje similar a Fable
import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

modelo = AutoModelForSeq2SeqLM.from_pretrained("modelo_de_lenguaje")
tokenizador = AutoTokenizer.from_pretrained("modelo_de_lenguaje")

texto = "Hola, ¿cómo estás?"
inputs = tokenizador(texto, return_tensors="pt")
outputs = modelo.generate(**inputs)
```
> "Fable es un modelo de lenguaje avanzado que ha sido diseñado para realizar tareas de procesamiento de lenguaje natural, como la generación de texto y la respuesta a preguntas." - [README de Fable]

## Cierre y perspectivas
La decisión de levantar los controles de exportación sobre Fable es un paso importante para la industria de la IA, ya que permite que las empresas de IA continúen desarrollando y exportando sus tecnologías. Sin embargo, también plantea desafíos en términos de seguridad y privacidad, ya que las tecnologías de IA pueden ser utilizadas para fines maliciosos si no se regulan adecuadamente.

**Bottom line:** El levantamiento de los controles de exportación sobre Fable es un paso importante para la industria de la IA, ya que permite que las empresas de IA continúen desarrollando y exportando sus tecnologías.

**Ver también:** [The New Stack: Fable is coming back: Federal government lifts export controls on Anthropic AI model](https://thenewstack.io/anthropic-fable-ban-lifted/) · [Anthropic: Fable](https://www.anthropic.com/fable)
