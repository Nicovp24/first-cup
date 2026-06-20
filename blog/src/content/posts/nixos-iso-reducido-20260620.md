---
title: "Nixos Iso Reducido"
date: "2026-06-20"
description: "La reducción del tamaño de las imágenes ISO de NixOS puede hacer que el sistema operativo sea más accesible para los usuarios que necesitan instalarlo en dispositivos con recursos limitados."
tags: ["NixOS", "open-source", "infraestructura"]
cover: "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://natkr.com/2026-06-19-nixos-but-smol/"
---

Un usuario ha publicado una entrada en su blog titulado [I can haz smoller NixOS ISOs?](https://natkr.com/2026-06-19-nixos-but-smol/), donde plantea la posibilidad de reducir el tamaño de las imágenes ISO de NixOS, un sistema operativo basado en el gestor de paquetes Nix. Esto ha generado interés en la comunidad, ya que NixOS es conocido por su enfoque en la reproducibilidad y la configuración declarativa, pero también por sus imágenes ISO relativamente grandes. La entrada ha sido publicada en el sitio web lobste.rs, donde ha recibido una estrella y algunos comentarios.

## Qué es / Qué ha pasado
El autor de la entrada plantea la posibilidad de reducir el tamaño de las imágenes ISO de NixOS, lo que podría ser beneficioso para los usuarios que necesitan instalar el sistema operativo en dispositivos con recursos limitados. NixOS es un sistema operativo basado en el gestor de paquetes Nix, que se enfoca en la reproducibilidad y la configuración declarativa. Sin embargo, las imágenes ISO de NixOS suelen ser relativamente grandes, lo que puede ser un problema para los usuarios que necesitan instalar el sistema operativo en dispositivos con recursos limitados. El autor no proporciona una solución específica, pero plantea la pregunta de si es posible reducir el tamaño de las imágenes ISO de NixOS.

## Por qué importa ahora
La reducción del tamaño de las imágenes ISO de NixOS es importante porque puede hacer que el sistema operativo sea más accesible para los usuarios que necesitan instalarlo en dispositivos con recursos limitados. Además, la tendencia hacia la computación en la nube y el uso de dispositivos de baja potencia ha aumentado en los últimos años, lo que ha generado un mayor interés en los sistemas operativos ligeros y eficientes. NixOS, con su enfoque en la reproducibilidad y la configuración declarativa, es un sistema operativo que puede ser atractivo para los usuarios que buscan una alternativa a los sistemas operativos tradicionales. Sin embargo, su tamaño relativamente grande puede ser un obstáculo para su adopción en dispositivos con recursos limitados.

## Detalles técnicos y qué significa para ti
La reducción del tamaño de las imágenes ISO de NixOS requeriría una reevaluación de los paquetes y las dependencias que se incluyen en la imagen. Esto podría implicar la eliminación de paquetes no esenciales o la optimización de los paquetes para que ocupen menos espacio. Por ejemplo, se podría utilizar una herramienta como `nix-build` para construir la imagen ISO y luego utilizar `nix-store` para optimizar los paquetes y reducir su tamaño.
```bash
nix-build -A config.system.build.isoImage
nix-store --optimize
```
> "La imagen ISO de NixOS puede ser grande debido a la cantidad de paquetes que se incluyen. Sin embargo, es posible reducir el tamaño de la imagen ISO eliminando paquetes no esenciales o optimizando los paquetes para que ocupen menos espacio." - README de NixOS

La reducción del tamaño de las imágenes ISO de NixOS podría ser beneficioso para los usuarios que necesitan instalar el sistema operativo en dispositivos con recursos limitados. Sin embargo, también podría requerir una reevaluación de los paquetes y las dependencias que se incluyen en la imagen, lo que podría afectar la funcionalidad del sistema operativo.

**Bottom line:** La reducción del tamaño de las imágenes ISO de NixOS es una cuestión importante que puede hacer que el sistema operativo sea más accesible para los usuarios que necesitan instalarlo en dispositivos con recursos limitados.

**Ver también:** [I can haz smoller NixOS ISOs?](https://natkr.com/2026-06-19-nixos-but-smol/) · [NixOS](https://nixos.org/)
