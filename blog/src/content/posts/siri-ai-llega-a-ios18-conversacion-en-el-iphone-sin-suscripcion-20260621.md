---
title: "Siri AI llega a iOS 18: conversación en el iPhone sin suscripción"
date: "2026-06-21"
description: "Apple incorpora Siri AI en iOS 18, permitiendo conversaciones de varios turnos y tareas encadenadas en el iPhone, con inferencia local y sin suscripción."
tags: ["IA", "tendencias", "Dev"]
cover: "https://media.wired.com/photos/6a33443c27f7de3a00911dff/191:100/w_1280,c_limit/Gear_TestingSiriAI-v1.jpg"
source_urls:
  - "https://www.wired.com/story/siri-ai-hands-on-iphone/"
---

El nuevo Siri AI genera respuestas en formato conversación y ya está disponible para todos los iPhone con iOS 18, sin necesidad de suscripciones adicionales. La actualización transforma a Siri de un asistente por comandos a un interlocutor capaz de mantener diálogos de varios turnos y de actuar en múltiples aplicaciones con una sola petición. La prueba práctica está en el artículo de *Wired* “Siri AI Hands On: A Smart, Helpful Assistant”.

## Qué es Siri AI y qué ha cambiado
Apple presentó Siri AI en la WWDC 2026 como una capa generativa basada en un modelo de lenguaje propio, integrado directamente en iOS 18. El asistente ahora interpreta contextos que abarcan varios turnos y puede ejecutar tareas encadenadas, como reservar una mesa, enviar un mensaje y consultar el tráfico, todo a partir de una única solicitud verbal. A diferencia de la versión anterior, que requería comandos explícitos y aislados, la nueva Siri se comporta como un modelo de conversación al estilo de Google Gemini o Microsoft Copilot, pero con la ventaja de la privacidad que ofrece el procesamiento mayoritariamente en el dispositivo.

## Por qué importa ahora
Durante los últimos años los asistentes de voz han quedado rezagados frente a los LLM de propósito general, porque sus respuestas eran limitadas y fragmentarias. La llegada de modelos generativos a los ecosistemas móviles ha sido impulsada por la demanda de interacciones más naturales y por la necesidad de reducir la fricción entre aplicaciones. Apple ha respondido a esta presión con una arquitectura que combina la potencia del Neural Engine y la optimización de modelos de varios miles de millones de parámetros, permitiendo que la inferencia se realice localmente sin sacrificar la calidad. La estrategia se alinea con la tendencia de “edge AI” que también está viendo a NVIDIA lanzar su Jetson Orin y a Qualcomm lanzar la serie Snapdragon X Elite con capacidades de IA on‑device.

## Detalles técnicos y qué significa para ti
El modelo subyacente se entrena con datos de uso anónimo y se despliega mediante el framework **Apple Intelligence**, accesible a través de la nueva API `SiriKit` en Swift. Un ejemplo mínimo para lanzar una conversación con el asistente es:

```swift
import SiriKit

Siri.shared.startConversation(prompt: "¿Cuál será el clima mañana en Madrid?")
```

> “Siri ahora entiende el contexto de la conversación y puede completar tareas en una sola solicitud, manteniendo la privacidad al ejecutar la inferencia en el dispositivo,” declaró Tim Cook en el comunicado de prensa.

En la práctica, los desarrolladores pueden crear *Intents* personalizados que aprovechan la capacidad de Siri para rellenar datos a lo largo de la interacción, lo que simplifica la integración de flujos de trabajo complejos. La solución es adecuada cuando la latencia y la privacidad son críticas, pero no sustituye a los modelos de gran escala en la nube para casos de generación de contenido extensivo o razonamiento especializado.

## Perspectiva de adopción
Para los equipos de ingeniería, la disponibilidad inmediata de Siri AI en iOS 18 abre la puerta a la creación de interfaces conversacionales sin depender de SDK externos. Los flujos de trabajo que antes requerían varios pasos de reconocimiento de voz, análisis de intención y llamadas a APIs ahora pueden condensarse en un único `Intent`. No obstante, la solución sigue limitada a los dominios que Apple ha expuesto; los casos de uso que demandan conocimientos muy específicos o acceso a bases de datos externas seguirán necesitando infraestructuras híbridas. En entornos empresariales, la capacidad de combinar Siri con la suite de productividad de Apple (Calendario, Mail, Notas) permite automatizar procesos internos sin exponer datos sensibles a la nube.

**Bottom line:** Siri AI lleva la conversación a los dispositivos iOS, ofreciendo asistencia práctica y privada que cierra la brecha entre los asistentes tradicionales y los LLM de escritorio.  

**Ver también:** [Apple presenta iOS 18 con Siri AI](https://www.apple.com/newsroom/2026/06/ios-18-launch) · [Google Gemini vs. Siri AI: comparativa de capacidades](https://www.theverge.com/2026/06/compare-gemini-siri)
