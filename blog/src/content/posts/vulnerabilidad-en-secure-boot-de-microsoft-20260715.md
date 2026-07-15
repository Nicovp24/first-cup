---
title: "Vulnerabilidad en Secure Boot de Microsoft"
date: "2026-07-15"
description: "La función Secure Boot de Microsoft ha estado comprometida durante una década debido a 'shims' antiguos y olvidados que permiten bypassar la verificación de seguridad."
tags: ["seguridad", "infraestructura", "Microsoft"]
cover: "https://cdn.arstechnica.net/wp-content/uploads/2026/07/computer-start-button-1152x648.jpg"
source_urls:
  - "https://arstechnica.com/security/2026/07/microsoft-secure-boot-has-been-broken-for-most-of-its-existence/"
---

La función Secure Boot de Microsoft ha estado comprometida durante una década sin que nadie se diera cuenta hasta ahora. Esto se debe a "shims" antiguos y olvidados que Microsoft no revocó, lo que ha simplificado los bypass de Secure Boot. Según un [artículo en Ars Technica](https://arstechnica.com/security/2026/07/microsoft-secure-boot-has-been-broken-for-most-of-its-existence/), esta vulnerabilidad ha estado presente durante la mayor parte de la existencia de Secure Boot, lo que plantea serias preocupaciones sobre la seguridad de los sistemas que confían en esta tecnología. La pregunta es, ¿qué es exactamente Secure Boot y por qué esta vulnerabilidad es tan importante ahora?

## Qué es / Qué ha pasado
Secure Boot es una característica de seguridad que verifica la autenticidad del firmware y del sistema operativo antes de arrancar el sistema. Esto se hace para prevenir que el malware se cargue durante el arranque y comprometa el sistema. Sin embargo, debido a los "shims" olvidados, los atacantes pueden bypassar esta verificación y cargar código malicioso. Los "shims" son componentes de software que se utilizan para adaptar el firmware y el sistema operativo a los requisitos de Secure Boot. En este caso, los "shims" antiguos y olvidados han sido utilizados para crear exploits que permiten a los atacantes cargar código malicioso sin ser detectados.

## Por qué importa ahora
La vulnerabilidad de Secure Boot es importante porque afecta a una amplia gama de sistemas, incluyendo PCs y servidores. La seguridad de estos sistemas es crucial, especialmente en entornos empresariales y gubernamentales donde se almacenan datos sensibles. La falta de conciencia sobre esta vulnerabilidad durante tanto tiempo es preocupante, ya que los atacantes podrían haber estado explotándola sin ser detectados. La noticia de esta vulnerabilidad refuerza la tendencia de que la seguridad informática es un tema complejo y en constante evolución, y que las soluciones de seguridad deben ser revisadas y actualizadas regularmente para mantenerse por delante de los atacantes.

## Detalles técnicos y qué significa para ti
La arquitectura de Secure Boot se basa en una cadena de confianza que verifica la autenticidad del firmware y del sistema operativo. Los "shims" se utilizan para adaptar esta cadena de confianza a los requisitos específicos de cada sistema. Sin embargo, los "shims" antiguos y olvidados han sido utilizados para crear exploits que rompen esta cadena de confianza. Por ejemplo, un atacante podría utilizar un "shim" malicioso para cargar un firmware modificado que permita cargar código malicioso durante el arranque. 
```bash
# Ejemplo de cómo un "shim" malicioso podría ser utilizado para cargar firmware modificado
sudo shim --firmware=malo.efi
```
> "Los 'shims' antiguos y olvidados han sido utilizados para crear exploits que permiten a los atacantes cargar código malicioso sin ser detectados." - Ars Technica.
Las implicaciones prácticas de esta vulnerabilidad son que los administradores de sistemas deben revisar y actualizar sus configuraciones de Secure Boot para asegurarse de que estén utilizando los "shims" más recientes y seguros. También deben considerar la posibilidad de utilizar soluciones de seguridad adicionales, como la autenticación multifactor, para proteger sus sistemas.

**Bottom line:** La vulnerabilidad de Secure Boot de Microsoft es un recordatorio de que la seguridad informática es un tema complejo y en constante evolución, y que las soluciones de seguridad deben ser revisadas y actualizadas regularmente para mantenerse por delante de los atacantes.
**Ver también:** [Microsoft’s Secure Boot has been broken for a decade and no one noticed until now](https://arstechnica.com/security/2026/07/microsoft-secure-boot-has-been-broken-for-most-of-its-existence/) · [Secure Boot en la documentación de Microsoft](https://docs.microsoft.com/es-es/windows-hardware/drivers/secureboot/secure-boot-overview)
