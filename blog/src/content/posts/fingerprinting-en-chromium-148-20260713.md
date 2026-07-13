---
title: "Fingerprinting en Chromium 148"
date: "2026-07-13"
description: "La función Math.tanh en Chromium 148 permite identificar el sistema operativo subyacente, lo que plantea preocupaciones sobre la privacidad y la seguridad en línea."
tags: ["seguridad", "JavaScript", "frontend"]
cover: "https://scrapfly.dev/img/og-default.png"
source_urls:
  - "https://scrapfly.dev/posts/browser-math-os-fingerprint/"
---

Desde la versión 148 de Chromium, la función `Math.tanh` es ahora fingerprintable, lo que permite vincular el sistema operativo subyacente. Esto significa que los desarrolladores web pueden identificar el sistema operativo de los usuarios de manera más precisa. [Más información sobre este cambio en el post de Scrapfly](https://scrapfly.dev/posts/browser-math-os-fingerprint/). La función `Math.tanh` es una de las muchas funciones matemáticas disponibles en JavaScript, y su comportamiento puede variar ligeramente entre diferentes sistemas operativos y navegadores. Esto ha llevado a los investigadores a explorar su potencial como un método de fingerprinting.

## Qué es / Qué ha pasado
El cambio en la función `Math.tanh` en Chromium 148 permite a los desarrolladores web identificar el sistema operativo subyacente de los usuarios mediante la detección de pequeñas variaciones en el comportamiento de la función. Esto se debe a que diferentes sistemas operativos y navegadores pueden implementar la función `Math.tanh` de manera ligeramente diferente, lo que puede ser detectado mediante pruebas cuidadosas. La capacidad de fingerprinting del sistema operativo subyacente puede tener implicaciones significativas para la privacidad y la seguridad en línea, ya que permite a los sitios web recopilar información más detallada sobre los usuarios.

## Por qué importa ahora
La capacidad de fingerprinting del sistema operativo subyacente es un tema que ha estado presente en la comunidad de seguridad en línea durante algún tiempo. La tendencia hacia una mayor personalización y segmentación de los usuarios en la web ha llevado a los sitios web a buscar métodos cada vez más sofisticados para recopilar información sobre los usuarios. Sin embargo, esto también plantea preocupaciones sobre la privacidad y la seguridad, ya que los usuarios pueden no estar al tanto de la cantidad de información que se está recopilando sobre ellos. El cambio en la función `Math.tanh` en Chromium 148 refuerza esta tendencia y destaca la necesidad de que los usuarios sean conscientes de las formas en que se recopila y utiliza su información en línea.

## Detalles técnicos y qué significa para ti
La función `Math.tanh` es una función matemática que devuelve el tangente hiperbólico de un número. En JavaScript, se puede utilizar para realizar cálculos matemáticos precisos. Sin embargo, el comportamiento de la función puede variar ligeramente entre diferentes sistemas operativos y navegadores, lo que la hace útil para el fingerprinting. Por ejemplo:
```javascript
console.log(Math.tanh(1.0));
```
Esto puede devolver resultados ligeramente diferentes en diferentes sistemas operativos y navegadores. 
> "La función `Math.tanh` puede ser utilizada para fingerprinting del sistema operativo subyacente debido a pequeñas variaciones en su comportamiento entre diferentes sistemas operativos y navegadores." 
En general, es importante ser consciente de las formas en que se recopila y utiliza la información en línea, y tomar medidas para proteger la privacidad y la seguridad en línea.

**Bottom line:** La capacidad de fingerprinting del sistema operativo subyacente a través de la función `Math.tanh` en Chromium 148 destaca la necesidad de que los usuarios sean conscientes de las formas en que se recopila y utiliza su información en línea.
**Ver también:** [Más información sobre el cambio en la función `Math.tanh` en Chromium 148](https://scrapfly.dev/posts/browser-math-os-fingerprint/) · [Información sobre la privacidad y la seguridad en línea](https://www.consumer.ftc.gov/topics/online-security)
