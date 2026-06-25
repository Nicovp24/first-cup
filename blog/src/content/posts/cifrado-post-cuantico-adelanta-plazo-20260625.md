---
title: "Cifrado post-cuántico adelanta plazo"
date: "2026-06-25"
description: "La Casa Blanca adelanta el plazo para abandonar algoritmos de cifrado vulnerables a ataques cuánticos, cambiando la política de seguridad nacional."
tags: ["seguridad", "infraestructura", "cifrado"]
cover: "https://cdn.arstechnica.net/wp-content/uploads/2024/03/GettyImages-1070527780-1152x648.jpg"
source_urls:
  - "https://arstechnica.com/information-technology/2026/06/executive-order-bumps-up-deadline-to-move-off-quantum-vulnerable-crypto/"
---

La Casa Blanca ha adelantado drásticamente el plazo para abandonar los algoritmos de cifrado vulnerables a ataques cuánticos, lo que supone un cambio significativo en la política de seguridad nacional. Esto se debe a la creciente preocupación por los riesgos de seguridad que plantean los algoritmos de cifrado actuales frente a la potencial capacidad de los ordenadores cuánticos para romperlos. La noticia se ha dado a conocer a través de un [artículo en Ars Technica](https://arstechnica.com/information-technology/2026/06/executive-order-bumps-up-deadline-to-move-off-quantum-vulnerable-crypto/), que detalla la orden ejecutiva y sus implicaciones.

## Qué es / Qué ha pasado
La orden ejecutiva empuja a las agencias gubernamentales y a las empresas que trabajan con ellas a migrar hacia algoritmos de cifrado post-cuánticos, que son resistentes a los ataques de los ordenadores cuánticos. Esto supone un desafío significativo, ya que la mayoría de los algoritmos de cifrado actuales se basan en la factorización de números grandes o en el logaritmo discreto, problemas que pueden ser resueltos de manera eficiente por un ordenador cuántico. La migración hacia algoritmos post-cuánticos requerirá cambios significativos en la infraestructura de seguridad de muchas organizaciones.

## Por qué importa ahora
La creciente potencia de los ordenadores cuánticos ha llevado a una creciente preocupación sobre la seguridad de los algoritmos de cifrado actuales. La capacidad de romper los algoritmos de cifrado utilizados en la mayoría de las transacciones en línea y en la comunicación segura supone un riesgo significativo para la seguridad nacional y la privacidad de los ciudadanos. La industria de la seguridad ha estado trabajando en el desarrollo de algoritmos post-cuánticos durante varios años, pero la migración hacia estos nuevos algoritmos ha sido lenta debido a la complejidad del cambio y la falta de estándares claros.

## Detalles técnicos y qué significa para ti
La migración hacia algoritmos post-cuánticos requerirá cambios significativos en la forma en que se implementa la seguridad en las aplicaciones y sistemas. Uno de los algoritmos post-cuánticos más prometedores es el algoritmo de firma digital basado en la lógica cuántica, que utiliza la mecánica cuántica para generar claves de cifrado seguras. 
```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Generar una clave RSA
clave_privada = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)
```
> "La seguridad de los algoritmos de cifrado actuales se basa en la dificultad de resolver ciertos problemas matemáticos, como la factorización de números grandes. Sin embargo, los ordenadores cuánticos pueden resolver estos problemas de manera eficiente, lo que supone un riesgo significativo para la seguridad de la información", según un experto en criptografía.

## Cierre
**Bottom line:** La Casa Blanca ha adelantado drásticamente el plazo para abandonar los algoritmos de cifrado vulnerables a ataques cuánticos, lo que supone un cambio significativo en la política de seguridad nacional y un desafío para la industria de la seguridad.

**Ver también:** [Ars Technica: White House drastically shortens deadline for dropping quantum-vulnerable crypto](https://arstechnica.com/information-technology/2026/06/executive-order-bumps-up-deadline-to-move-off-quantum-vulnerable-crypto/) · [NIST: Post-Quantum Cryptography](https://csrc.nist.gov/projects/post-quantum-cryptography)
