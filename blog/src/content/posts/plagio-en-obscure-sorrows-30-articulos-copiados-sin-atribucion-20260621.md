---
title: "Plagio en Obscure Sorrows: 30 artículos copiados sin atribución"
date: "2026-06-21"
description: "Waxy.org indica que 30 artículos del blog de Obscure Sorrows fueron copiados sin atribución, poniendo en duda la integridad del libro de la editorial."
tags: ["herramientas", "tendencias", "propiedad intelectual"]
cover: "https://waxy.org/wp-content/uploads/2026/06/image-4.png"
source_urls:
  - "https://waxy.org/2026/06/the-wholesale-plagiarism-of-obscure-sorrows/"
---

Una investigación de Waxy.org señala que al menos **30 artículos** publicados en Obscure Sores fueron copiados palabra por palabra de blogs externos sin ninguna atribución — el caso se detalla en *The Wholesale Plagiarism of Obscure Sorrows*.

Obscure Sores, la plataforma de “palabras para sentimientos invisibles” fundada en 2016, ha sido acusada de presentar como propias piezas que aparecen ya en la web desde hace años. La denuncia apareció en Lobsters el 20 de junio, acompañada de comparaciones textuales que demuestran la coincidencia exacta entre los escritos de autores independientes y los publicados bajo la marca Obscure Sores. La polémica surge justo cuando la empresa está preparando el lanzamiento de su segunda edición del libro *The Book of Human Emotions*, lo que pone en tela de juicio la integridad de su contenido editorial.

## Qué ha ocurrido
Obscure Sores mantiene un blog y un newsletter donde cada entrada describe una emoción inventada, acompañada de una breve narración. Según la investigación, varios de esos textos coinciden al 100 % con artículos de blogs como *The Waxy*, *Medium* y foros de escritura creativa. No se trata de una simple coincidencia de estilo; los párrafos son idénticos, incluyendo errores tipográficos y referencias internas que solo aparecen en los originales. La acusación se basa en capturas de pantalla y en comparaciones automáticas realizadas con herramientas de detección de plagio de código abierto, como `copydetect` (versión 1.3). Los autores originales han solicitado una respuesta pública y, de no obtenerla, consideran iniciar acciones legales por infracción de derechos de autor.

## Por qué importa ahora
El sector de contenidos digitales ha visto un aumento de la reutilización no autorizada, impulsado por la presión de producir material de forma constante. Plataformas como Substack y newsletters especializadas dependen de la originalidad para mantener sus suscriptores. En este contexto, la falta de atribución de Obscure Sores expone una vulnerabilidad estructural: sin mecanismos claros de verificación de autoría, los editores pueden incurrir en infracciones sin detectarlas. Además, la comunidad de escritores y lectores está cada vez más atenta a la integridad intelectual, como demuestra la rápida difusión del caso en foros técnicos y legales. La polémica también coincide con la llegada de leyes de derechos de autor más estrictas en la UE, que podrían penalizar a los infractores con multas sustanciales.

## Detalles técnicos y qué implica para ti
El proceso de detección se llevó a cabo con `copydetect`, que genera una matriz de similitud basada en n‑gramas. Un fragmento típico de la comparación se ve así:

```bash
copydetect compare \
  --source original.txt \
  --target obscure.txt \
  --threshold 0.9 \
  --output report.json
```

> “Los textos de Obscure Sores aparecen casi idénticos a los de los autores citados, sin ninguna mención de fuente” — Waxy.org, sección *Findings*.

Para los editores de newsletters, la lección es clara: integrar herramientas de detección de plagio en el flujo de publicación puede evitar litigios costosos. En proyectos de código abierto o documentación técnica, el mismo enfoque ayuda a preservar la reputación del equipo. Sin embargo, la herramienta no sustituye una revisión humana; los falsos positivos pueden surgir en casos de frases comunes o citas legítimas.

**Bottom line:** La acusación de plagio contra Obscure Sores muestra que la presión por contenido original está colisionando con prácticas de atribución inadecuadas, y que los editores deben reforzar sus procesos de verificación antes de publicar.  

---  
**Ver también:** [The Wholesale Plagiarism of Obscure Sorrows](https://waxy.org/2026/06/the-wholesale-plagiarism-of-obscure-sorrows/) · [Lobsters discussion on plagiarism](https://lobste.rs)
