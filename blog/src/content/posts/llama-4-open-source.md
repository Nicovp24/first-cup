---
title: "Llama 4 Scout: Meta lanza un modelo de 17B que rival a GPT-4o en código"
date: "2026-05-20"
description: "Meta publicó Llama 4 Scout, un modelo de 17 mil millones de parámetros con Mixture-of-Experts que supera a GPT-4o en HumanEval y MBPP. Pesos libres, licencia comercial permisiva."
tags: ["IA", "open-source", "LLMs"]
cover: "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=800&q=75"
source_urls:
  - "https://ai.meta.com"
  - "https://huggingface.co"
  - "https://arxiv.org"
---

## Qué hace especial a Scout

Llama 4 Scout usa una arquitectura Mixture-of-Experts (MoE) con 17B de parámetros activos por token, pero 109B de parámetros totales. Esto le da la eficiencia de inferencia de un modelo pequeño con la calidad de uno mucho mayor.

**Benchmarks:**
- HumanEval (generación de código): **89.3%** vs GPT-4o **87.1%**
- MBPP: **82.7%** vs GPT-4o **81.2%**
- MMLU: **86.1%** (similar a GPT-4o)
- Velocidad en A100: ~180 tokens/segundo (2.4x más rápido que Llama 3.1 405B)

## La importancia del open source aquí

El modelo se publica con licencia Llama 4 Community License — comercialmente usable para la mayoría de casos (excepto competidores directos con >700M usuarios activos). Los pesos están en Hugging Face desde el día 1.

Esto significa que cualquier empresa puede:
- Hacer fine-tuning sobre sus propios datos
- Deployar en su infraestructura sin pagar por token
- Modificar y redistribuir (con restricciones)

## Cómo probarlo ahora

```bash
# Con Ollama (la forma más rápida)
ollama pull llama4:scout
ollama run llama4:scout

# Con la API de Hugging Face
pip install transformers
# modelo: meta-llama/Llama-4-Scout-17B-16E-Instruct
```

---

**Bottom line:** Para empresas que procesan datos sensibles o volúmenes altos, Scout cambia la ecuación económica. Un buen modelo de código que puedes correr on-premise es un game changer para equipos de desarrollo.
