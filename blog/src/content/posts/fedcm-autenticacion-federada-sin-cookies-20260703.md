---
title: "FedCM: Autenticación federada sin cookies"
date: "2026-07-03"
description: "FedCM ofrece una alternativa segura y privada a los botones de inicio de sesión social tradicionales, mejorando la experiencia del usuario y reduciendo la dependencia de las cookies de terceros."
tags: ["seguridad", "autenticación", "open-source"]
cover: "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://thenewstack.io/fedcm-federated-login-standard/"
---

El 95% de los sitios web utilizan botones de inicio de sesión social que dependen de cookies de terceros, lo que plantea serios problemas de privacidad y seguridad. Sin embargo, FedCM, un nuevo estándar de inicio de sesión federado, ofrece una alternativa que no requiere cookies de terceros. Esto es especialmente relevante en el contexto de la creciente preocupación por la privacidad en línea y las restricciones sobre el uso de cookies. Puedes leer más sobre este tema en [el artículo original de The New Stack](https://thenewstack.io/fedcm-federated-login-standard/).

## Qué es / Qué ha pasado
FedCM es un estándar de inicio de sesión federado que permite a los usuarios iniciar sesión en sitios web sin tener que revelar su información personal a terceros. A diferencia de los botones de inicio de sesión social tradicionales, como "Iniciar sesión con Google" o "Continuar con Apple", que utilizan cookies de terceros para autenticar a los usuarios, FedCM utiliza un enfoque más seguro y privado. Este enfoque se basa en la autenticación descentralizada, lo que significa que los usuarios pueden controlar sus propias credenciales y decidir con quién comparten su información.

## Por qué importa ahora
La importancia de FedCM radica en su capacidad para abordar los problemas de privacidad y seguridad que plantean las cookies de terceros. En la actualidad, las cookies de terceros se utilizan ampliamente para rastrear a los usuarios en línea y recopilar datos sobre su comportamiento, lo que ha generado una gran preocupación entre los defensores de la privacidad. Además, las restricciones sobre el uso de cookies, como el Reglamento General de Protección de Datos (RGPD) de la Unión Europea, han hecho que las empresas busquen alternativas más seguras y privadas para autenticar a los usuarios. FedCM se posiciona como una solución atractiva en este contexto, ya que ofrece una forma más segura y privada de autenticar a los usuarios sin comprometer su experiencia en línea.

## Detalles técnicos y qué significa para ti
La arquitectura de FedCM se basa en la autenticación descentralizada, lo que significa que los usuarios pueden controlar sus propias credenciales y decidir con quién comparten su información. Esto se logra a través de la utilización de tokens de autenticación que se emiten por el proveedor de identidad y se verifican por el sitio web que solicita la autenticación. 
```python
# Ejemplo de cómo utilizar FedCM para autenticar a un usuario
import requests

# Solicitar token de autenticación
response = requests.post('https://example.com/authenticate', data={'username': 'usuario', 'password': 'contraseña'})

# Verificar token de autenticación
if response.status_code == 200:
    token = response.json()['token']
    # Utilizar token para acceder a recursos protegidos
    response = requests.get('https://example.com/protected-resource', headers={'Authorization': f'Bearer {token}'})
```
> "FedCM ofrece una forma más segura y privada de autenticar a los usuarios sin comprometer su experiencia en línea", según el [README de FedCM](https://github.com/fedcm/fedcm).

## Implicaciones prácticas
Las implicaciones prácticas de FedCM son significativas, ya que ofrece una forma más segura y privada de autenticar a los usuarios. Esto puede ser especialmente útil para aplicaciones que requieren un alto nivel de seguridad, como las aplicaciones financieras o de salud. Además, FedCM puede ayudar a reducir la dependencia de las cookies de terceros, lo que puede mejorar la experiencia del usuario y reducir la cantidad de datos que se recopilan sobre ellos.

**Bottom line:** **FedCM ofrece una alternativa más segura y privada a los botones de inicio de sesión social tradicionales, lo que puede mejorar la experiencia del usuario y reducir la dependencia de las cookies de terceros.**
**Ver también:** [The New Stack: FedCM](https://thenewstack.io/fedcm-federated-login-standard/) · [FedCM en GitHub](https://github.com/fedcm/fedcm)
