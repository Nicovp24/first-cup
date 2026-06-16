---
title: "Puerta trasera en oferta de trabajo de LinkedIn"
date: "2026-06-16"
description: "Un desarrollador descubrió una puerta trasera en una oferta de trabajo de LinkedIn que podría haber permitido el acceso no autorizado a la red de la empresa."
tags: ["seguridad", "Dev", "LinkedIn"]
cover: "https://roman.pt/posts/linkedin-backdoor/splash.png"
source_urls:
  - "https://roman.pt/posts/linkedin-backdoor/"
---

Un total de 1.151 estrellas han marcado la historia de un ingeniero que descubrió una puerta trasera en una oferta de trabajo de LinkedIn. La historia, publicada en el blog de Roman, detalla cómo un desarrollador recibió una oferta de trabajo que incluía un proyecto de prueba que, en realidad, era una puerta trasera para acceder a la red de la empresa. Puedes leer más sobre este incidente en [A backdoor in a LinkedIn job offer](https://roman.pt/posts/linkedin-backdoor/). Esto ha generado una gran preocupación en la comunidad de desarrolladores y seguridad, ya que destaca la importancia de verificar la autenticidad de las ofertas de trabajo y los proyectos que se reciben.

## Qué es / Qué ha pasado
El incidente se refiere a una oferta de trabajo que se envió a un desarrollador a través de la plataforma de LinkedIn. La oferta incluía un proyecto de prueba que, en realidad, era una puerta trasera para acceder a la red de la empresa. El desarrollador, que no ha sido identificado, descubrió la puerta trasera y denunció el incidente en su blog. La historia ha generado una gran preocupación en la comunidad de desarrolladores y seguridad, ya que destaca la importancia de verificar la autenticidad de las ofertas de trabajo y los proyectos que se reciben. El proyecto de prueba en cuestión parecía ser un ejemplo de un proyecto legítimo, pero en realidad era una herramienta maliciosa diseñada para obtener acceso no autorizado a la red de la empresa.

## Por qué importa ahora
La seguridad en la contratación de personal es un tema que ha estado presente en la industria durante mucho tiempo. Sin embargo, la creciente dependencia de las plataformas en línea para encontrar y contratar talentos ha aumentado el riesgo de este tipo de incidentes. La tendencia hacia el trabajo remoto y la contratación de freelancers ha creado un entorno en el que los ataques de phishing y las puertas traseras pueden ser más fáciles de ejecutar. Además, la falta de transparencia en el proceso de contratación y la ausencia de medidas de seguridad adecuadas pueden hacer que sea más difícil detectar y prevenir este tipo de incidentes. La comunidad de desarrolladores y seguridad debe estar alerta y tomar medidas para protegerse contra este tipo de ataques.

## Detalles técnicos y qué significa para ti
La puerta trasera en cuestión se disfrazaba de un proyecto de prueba legítimo, pero en realidad era una herramienta maliciosa diseñada para obtener acceso no autorizado a la red de la empresa. El proyecto de prueba incluía un código que, una vez ejecutado, permitía al atacante acceder a la red de la empresa y obtener información confidencial. 
```bash
# Ejemplo de cómo podría haberse implementado la puerta trasera
# (Nota: Esto es solo un ejemplo y no debe ser utilizado en producción)
nc -l -p 8080 -e /bin/bash
```
> "La puerta trasera se disfrazaba de un proyecto de prueba legítimo, pero en realidad era una herramienta maliciosa diseñada para obtener acceso no autorizado a la red de la empresa." - Roman, autor del blog.

La implicación práctica de este incidente es que los desarrolladores deben ser extremadamente cautelosos al recibir ofertas de trabajo y proyectos que incluyan código o instrucciones que no sean claras o que parezcan sospechosas. Es importante verificar la autenticidad de la oferta y del proyecto, y no ejecutar código que no se haya verificado previamente.

**Bottom line:** La seguridad en la contratación de personal es un tema crítico que requiere atención inmediata, ya que la creciente dependencia de las plataformas en línea para encontrar y contratar talentos ha aumentado el riesgo de incidentes de seguridad.

**Ver también:** [A backdoor in a LinkedIn job offer](https://roman.pt/posts/linkedin-backdoor/) · [Guía de seguridad para desarrolladores](https://www owasp.org/index.php/Guide_to_Authentication)
