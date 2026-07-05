---
title: "Safari incorpora Protocolo de Contexto de Modelo"
date: "2026-07-05"
description: "Apple integra el Protocolo de Contexto de Modelo en Safari para permitir la interacción con inteligencia artificial y mejorar la personalización de experiencias de usuario en sus productos y servicios."
tags: ["IA", "Dev", "herramientas", "open-source"]
cover: "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/safari-mcp-platform-infrastructure/"
---

Apple acaba de incorporar un servidor de Protocolo de Contexto de Modelo (MCP) en su navegador Safari, lo que permite a los agentes de inteligencia artificial controlar el navegador. Esto se ha implementado en la versión de preview 247 de Safari Technology Preview, y se puede [leer más al respecto en el artículo de The New Stack](https://thenewstack.io/safari-mcp-platform-infrastructure/). La incorporación de esta tecnología sugiere que Apple está explorando nuevas formas de integrar la inteligencia artificial en sus productos y servicios. Esto podría ser un paso hacia la creación de experiencias de usuario más personalizadas y automatizadas en el futuro.

## Qué es el Protocolo de Contexto de Modelo
El Protocolo de Contexto de Modelo es un estándar que permite a los agentes de inteligencia artificial interactuar con aplicaciones y servicios web de manera más efectiva. Esto se logra mediante la creación de un contexto compartido entre el agente y la aplicación, lo que permite una comunicación más fluida y precisa. En el caso de Safari, la incorporación de este protocolo significa que los desarrolladores pueden crear agentes de inteligencia artificial que puedan controlar el navegador y realizar tareas de manera automática. El proyecto de Safari Technology Preview es un repositorio de código abierto que se encuentra en [webkit/webkit](https://github.com/webkit/webkit), con más de 13.000 estrellas en GitHub, y está escrito principalmente en C++.

## Por qué importa ahora
La incorporación del Protocolo de Contexto de Modelo en Safari es importante porque refleja una tendencia en la industria hacia la integración de la inteligencia artificial en los productos y servicios web. Esto se debe en parte a la creciente demanda de experiencias de usuario más personalizadas y automatizadas. Los desarrolladores y las empresas están buscando formas de aprovechar la inteligencia artificial para mejorar la eficiencia y la efectividad de sus aplicaciones y servicios. La incorporación de este protocolo en Safari sugiere que Apple está comprometida con esta tendencia y está trabajando para proporcionar a los desarrolladores las herramientas y las tecnologías necesarias para crear experiencias de usuario más avanzadas. Otros proyectos relacionados, como el proyecto de [Mozilla](https://github.com/mozilla) para integrar la inteligencia artificial en sus productos, también están avanzando en esta dirección.

## Detalles técnicos y qué significa para ti
La arquitectura del Protocolo de Contexto de Modelo se basa en la creación de un contexto compartido entre el agente de inteligencia artificial y la aplicación web. Esto se logra mediante la utilización de una API que permite al agente interactuar con la aplicación de manera más efectiva. Por ejemplo, se puede utilizar el siguiente código para establecer una conexión con el servidor de MCP:
```javascript
const MCPClient = require('mcp-client');
const client = new MCPClient('https://example.com/mcp');
client.connect().then(() => {
  console.log('Conectado al servidor de MCP');
});
```
Según el [README del proyecto](https://github.com/webkit/webkit/blob/main/Source/JavaScriptCore/mcp/README.md), "el Protocolo de Contexto de Modelo es un estándar que permite a los agentes de inteligencia artificial interactuar con aplicaciones y servicios web de manera más efectiva". En términos prácticos, esto significa que los desarrolladores pueden crear agentes de inteligencia artificial que puedan controlar el navegador y realizar tareas de manera automática, lo que puede ser útil para tareas como la automatización de pruebas o la recopilación de datos.

**Bottom line:** La incorporación del Protocolo de Contexto de Modelo en Safari es un paso importante hacia la integración de la inteligencia artificial en los productos y servicios web de Apple.

**Ver también:** [Safari Technology Preview](https://webkit.org/downloads/) · [Protocolo de Contexto de Modelo](https://github.com/webkit/webkit/blob/main/Source/JavaScriptCore/mcp/README.md)
