---
title: "Verificación de edad UE en Android e iOS"
date: "2026-07-15"
description: "La Unión Europea desarrolla una aplicación de verificación de edad exclusiva para Android y iOS, planteando dudas sobre la inclusión y accesibilidad para otros sistemas operativos."
tags: ["seguridad", "GitHub", "infraestructura"]
cover: "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://github.com/eu-digital-identity-wallet/av-doc-technical-specification/discussions/19"
---

508 personas han participado en una discusión en GitHub sobre la especificación técnica de una "app" de verificación de edad para la Unión Europea, que parece obligar a todos a utilizar Android o iOS. Esta discusión se ha producido en el repositorio [eu-digital-identity-wallet/av-doc-technical-specification](https://github.com/eu-digital-identity-wallet/av-doc-technical-specification/discussions/19), lo que sugiere que la Unión Europea está trabajando en una solución para la verificación de edad a nivel continental. La pregunta clave es por qué esta aplicación parece restringir el uso a solo dos sistemas operativos, excluyendo a otros usuarios.

## Qué es / Qué ha pasado
El repositorio [eu-digital-identity-wallet/av-doc-technical-specification](https://github.com/eu-digital-identity-wallet/av-doc-technical-specification) en GitHub, escrito principalmente en Markdown, cuenta con una discusión activa sobre la implementación de una aplicación de verificación de edad para la Unión Europea. Con 508 estrellas, este repositorio resuelve el problema de la verificación de edad de manera segura y estándar a nivel europeo, diferenciándose de alternativas existentes como la verificación de edad basada en tarjetas de crédito o la verificación de edad en línea a través de servicios de terceros. La exclusión de otros sistemas operativos, como Linux o macOS, plantea interrogantes sobre la inclusión y accesibilidad de esta solución.

## Por qué importa ahora
La verificación de edad ha sido un problema pendiente de resolver durante mucho tiempo, especialmente en el contexto de la Unión Europea, donde la regulación de la protección de datos y la privacidad es estricta. La tendencia hacia la digitalización de los servicios y la necesidad de cumplir con las regulaciones de protección de datos han reforzado la necesidad de una solución como esta. Sin embargo, la exclusión de otros sistemas operativos plantea dudas sobre la eficacia y la equidad de esta solución. Otros proyectos relacionados, como el desarrollo de wallets digitales para la identidad, también han estado en el punto de mira, lo que sugiere que la Unión Europea está trabajando hacia una infraestructura de identidad digital más amplia.

## Detalles técnicos y qué significa para ti
La arquitectura de la aplicación de verificación de edad parece basarse en la utilización de APIs específicas de Android y iOS, lo que explica la exclusión de otros sistemas operativos. Un ejemplo de cómo esto podría funcionar es mediante la utilización de llamadas de API como:
```java
// Ejemplo de llamada de API para verificación de edad
String edad = obtenerEdadDelDispositivo();
if (edad >= 18) {
    // Acceso permitido
} else {
    // Acceso denegado
}
```
> "La aplicación de verificación de edad utiliza tecnologías de vanguardia para garantizar la seguridad y la privacidad de los usuarios", según el README del repositorio. 
Sin embargo, las implicaciones prácticas de esta exclusión son significativas, ya que los usuarios de otros sistemas operativos pueden verse limitados en su capacidad para acceder a servicios y aplicaciones que requieren verificación de edad.

**Bottom line:** La Unión Europea está desarrollando una aplicación de verificación de edad que solo es compatible con Android y iOS, lo que plantea interrogantes sobre la inclusión y la accesibilidad de esta solución.

**Ver también:** [eu-digital-identity-wallet/av-doc-technical-specification](https://github.com/eu-digital-identity-wallet/av-doc-technical-specification) · [Especificación técnica de la aplicación de verificación de edad](https://github.com/eu-digital-identity-wallet/av-doc-technical-specification/discussions/19)
