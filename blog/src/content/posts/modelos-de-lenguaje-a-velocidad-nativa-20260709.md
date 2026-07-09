---
title: "Modelos de lenguaje a velocidad nativa"
date: "2026-07-09"
description: "Hugging Face lanza un nuevo backend para modelos de lenguaje que permite la ejecución a velocidades similares a las de los modelos tradicionales, lo que puede cambiar la forma en que se utilizan en aplicaciones prácticas."
tags: ["IA", "LLMs", "Dev", "Python", "herramientas", "backend", "open-source"]
cover: "https://huggingface.co/blog/assets/native-speed-vllm-transformers-backend/thumbnail.png"
source_urls:
  - "https://huggingface.co/blog/native-speed-vllm-transformers-backend"
---

Hugging Face ha anunciado un nuevo backend de modelado de transformers para vLLM (Large Language Models) con velocidad nativa. Esto significa que los modelos de lenguaje pueden ejecutarse a velocidades similares a las de los modelos tradicionales, lo que puede revolucionar la forma en que se utilizan los modelos de lenguaje en aplicaciones prácticas. La noticia se puede encontrar en [el blog de Hugging Face](https://huggingface.co/blog/native-speed-vllm-transformers-backend), donde se explican los detalles técnicos y las implicaciones de esta innovación.

## Qué es / Qué ha pasado
El nuevo backend de Hugging Face se basa en una arquitectura de transformers que permite la ejecución de modelos de lenguaje a velocidades nativas. El repositorio de GitHub correspondiente es `huggingface/transformers`, con más de 70.000 estrellas, y está escrito principalmente en Python. Este backend resuelve el problema de la lentitud en la ejecución de modelos de lenguaje, lo que lo diferencia de alternativas existentes como `tensorflow` y `pytorch`. La principal ventaja de este backend es que permite la ejecución de modelos de lenguaje en tiempo real, lo que lo hace adecuado para aplicaciones como el procesamiento de lenguaje natural y la generación de texto.

## Por qué importa ahora
La ejecución de modelos de lenguaje a velocidades nativas es un problema que lleva tiempo sin resolverse. Los modelos de lenguaje actuales son muy grandes y complejos, lo que los hace lentos y difíciles de ejecutar. Esto ha limitado su uso en aplicaciones prácticas, como la traducción automática y la generación de texto. La tendencia actual en la investigación de modelos de lenguaje es hacia la creación de modelos más grandes y complejos, lo que hace que la velocidad de ejecución sea un problema cada vez más importante. El nuevo backend de Hugging Face refuerza esta tendencia y ofrece una solución a este problema. Otros proyectos relacionados, como `transformers` y `sentence-transformers`, también están trabajando en la mejora de la velocidad de ejecución de los modelos de lenguaje.

## Detalles técnicos y qué significa para ti
La arquitectura del nuevo backend de Hugging Face se basa en una combinación de técnicas de procesamiento de lenguaje natural y de aprendizaje automático. La API es simple y fácil de usar, y se puede instalar con el siguiente comando:
```python
pip install transformers
```
Según el README del repositorio, "el nuevo backend de transformers permite la ejecución de modelos de lenguaje a velocidades nativas, lo que lo hace adecuado para aplicaciones en tiempo real". 
> "Nuestro objetivo es proporcionar una forma fácil de usar y eficiente de ejecutar modelos de lenguaje, lo que permita a los desarrolladores crear aplicaciones innovadoras y útiles".
Las implicaciones prácticas de este backend son importantes, ya que permite la ejecución de modelos de lenguaje en tiempo real, lo que lo hace adecuado para aplicaciones como la traducción automática y la generación de texto.

**Bottom line:** **El nuevo backend de Hugging Face para vLLM transformers permite la ejecución de modelos de lenguaje a velocidades nativas, lo que puede revolucionar la forma en que se utilizan los modelos de lenguaje en aplicaciones prácticas**.
**Ver también:** [Hugging Face Blog: Native-speed vLLM transformers modeling backend](https://huggingface.co/blog/native-speed-vllm-transformers-backend) · [Repositorio de GitHub: huggingface/transformers](https://github.com/huggingface/transformers)
