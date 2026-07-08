---
title: "Hugging Face y SageMaker Studio se integran"
date: "2026-07-08"
description: "La integración permite desplegar modelos de aprendizaje automático con solo un clic, simplificando el proceso de despliegue y reduciendo la brecha entre el desarrollo y la producción."
tags: ["IA", "Dev", "herramientas"]
cover: "https://cdn-uploads.huggingface.co/production/uploads/68abb71b13d7773ad97e9035/f1nX3dXVmvJcQzJfgfpnJ.webp"
source_urls:
  - "https://huggingface.co/blog/amazon/one-click-to-sagemaker-studio"
---

Ahora es posible migrar modelos de Hugging Face a Amazon SageMaker Studio con solo un clic, gracias a la integración recientemente anunciada. Esto implica que los desarrolladores pueden aprovechar las capacidades de entrenamiento y despliegue de SageMaker sin necesidad de configuraciones manuales complejas. Para más información, se puede consultar el [blog de Hugging Face](https://huggingface.co/blog/amazon/one-click-to-sagemaker-studio), donde se detallan los pasos y beneficios de esta integración.

## Qué es / Qué ha pasado
La integración entre Hugging Face y Amazon SageMaker Studio permite a los desarrolladores desplegar modelos de aprendizaje automático entrenados en Hugging Face directamente en SageMaker, lo que facilita el proceso de inferencia y despliegue en producción. Hugging Face es una plataforma popular para el desarrollo y despliegue de modelos de lenguaje natural, mientras que SageMaker es una plataforma de aprendizaje automático en la nube ofrecida por Amazon Web Services (AWS). La integración elimina la necesidad de configurar manualmente el entorno de ejecución y las dependencias para los modelos, lo que reduce significativamente el tiempo y el esfuerzo necesarios para desplegar modelos en producción.

## Por qué importa ahora
La capacidad de desplegar modelos de aprendizaje automático de manera eficiente y escalable es crucial en la actualidad, dado el creciente uso de la inteligencia artificial en diversas industrias. La integración entre Hugging Face y SageMaker Studio refuerza la tendencia hacia la democratización del acceso a herramientas de aprendizaje automático avanzadas, permitiendo a más desarrolladores y organizaciones aprovechar el potencial de la inteligencia artificial sin necesidad de invertir en infraestructura y expertos especializados. Además, esta integración se produce en un momento en que la industria del aprendizaje automático está experimentando un crecimiento explosivo, con un mayor enfoque en la simplificación del proceso de despliegue y la reducción de la brecha entre el desarrollo y la producción.

## Detalles técnicos y qué significa para ti
La integración se basa en la API de SageMaker y las bibliotecas de Hugging Face, lo que permite una transición suave entre el entrenamiento y el despliegue de modelos. Para utilizar esta integración, los desarrolladores simplemente necesitan seleccionar el modelo deseado en Hugging Face y seguir las instrucciones para desplegarlo en SageMaker Studio. 
```python
# Ejemplo de cómo desplegar un modelo en SageMaker Studio
from sagemaker.huggingface import HuggingFace
huggingface_model = HuggingFace(
    entry_point='inference.py',
    source_dir='./src',
    role=get_execution_role(),
    transformers_version='4.24.0',
    py_version='py38',
    instance_type='ml.m5.xlarge'
)
```
> "Con esta integración, los desarrolladores pueden desplegar modelos de Hugging Face en SageMaker Studio con solo un clic, lo que simplifica significativamente el proceso de despliegue y permite a más organizaciones aprovechar el potencial de la inteligencia artificial." - [Hugging Face Blog](https://huggingface.co/blog/amazon/one-click-to-sagemaker-studio)

**Bottom line:** La integración entre Hugging Face y Amazon SageMaker Studio permite el despliegue de modelos de aprendizaje automático con solo un clic, simplificando significativamente el proceso de despliegue y reduciendo la brecha entre el desarrollo y la producción.

**Ver también:** [Integración de Hugging Face con Amazon SageMaker Studio](https://huggingface.co/blog/amazon/one-click-to-sagemaker-studio) · [Documentación de SageMaker](https://docs.aws.amazon.com/sagemaker/latest/dg/whatis.html)
