---
title: "Fruit Dash: platformer 2D con puertas lógicas binarias en Unity 2022.3"
date: "2026-06-21"
description: "Fruit Dash ganó el Solstice Game Jam con 24 votos y su código abierto en Unity 2022.3 muestra cómo añadir puertas lógicas binarias a un platformer 2D."
tags: ["Dev", "GitHub", "open-source", "Unity"]
cover: "https://media2.dev.to/dynamic/image/width=1200,height=627,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fkkd7d3pg8n19410xl550.png"
source_urls:
  - "https://dev.to/agastya_khati_f72c89077c8/fruit-dash-a-solstice-platformer-with-binary-code-gates-2jmi"
---

Fruit Dash ganó la primera posición del Solstice Game Jam con 24 votos en menos de 48 h. Es un platformer de 2 D construido en Unity 2022.3 LTS que introduce “binary code gates”: puertas que sólo se abren cuando el jugador activa la combinación exacta de bits representada por los objetos recogidos. La publicación en dev.to llega justo cuando la comunidad indie está explotando las mejoras de URP y los asset packs de lógica visual, lo que convierte a este proyecto en un caso de estudio de cómo una mecánica de bajo nivel puede escalar rápidamente a un juego completo.

## Qué es Fruit Dash y qué lo diferencia  
El proyecto está alojado en el repositorio **agastya‑khati/fruit‑dash** (GitHub) y está escrito mayoritariamente en C#. Con 24 estrellas en dev.to, se posiciona como una de las entregas más votadas del jam de junio 2026. La premisa básica es un corredor de frutas que debe atravesar plataformas mientras recoge “bits” (representados por distintas frutas) y los combina para desbloquear puertas lógicas. A diferencia de otros platformers del jam que se limitan a mecánicas de salto o velocidad, Fruit Dash implementa una capa de puzzle basada en operaciones binarias (AND, OR, XOR) directamente en el motor, sin necesidad de plugins externos. En la escena de ejemplo, la puerta A solo se abre si el jugador lleva una manzana (bit 0) y una cereza (bit 2), mientras que la puerta B requiere la combinación XOR de piña y plátano.

## Por qué importa ahora  
Los desarrolladores indie han estado buscando formas de añadir profundidad sin inflar la carga de trabajo. Desde la publicación de Unity 2022.3, el pipeline de renderizado URP permite iterar rápidamente con shaders ligeros, y los asset packs de lógica visual (por ejemplo, “Logic Gate Pack” en la Asset Store) han normalizado el uso de puertas lógicas en juegos de plataformas. Sin embargo, pocos proyectos integran esa lógica a nivel de código, lo que obliga a scripts ad‑hoc y a duplicar código. Fruit Dash muestra una solución reutilizable: un componente genérico que interpreta una máscara de bits y la compara con la entrada del jugador. Esa aproximación encaja con la tendencia de “code‑first” en los jams, donde la rapidez de prototipado se mide en líneas de código más que en assets.

En paralelo, la comunidad de Game Jam ha visto crecer la práctica de “puzzle‑platformer hybrid”, con títulos como *Bit‑Runner* (Ludum Dare 50) y *Gatekeeper* (Global Game Jam 2025) que exploran mecánicas similares. Fruit Dash aporta una referencia concreta y abierta que otros pueden forkear para experimentar con combinaciones más complejas o adaptar a géneros distintos, como metroidvania o roguelike.

## Detalles técnicos y qué significa para ti  
El núcleo está en el script **BinaryGate.cs**, que expone dos campos en el inspector: `requiredMask` (int) y `gateType` (enum: AND, OR, XOR). Durante la colisión con el jugador, el script lee la variable `playerBits` del componente **PlayerInventory** y evalúa la condición:

```csharp
public enum GateType { AND, OR, XOR }

public class BinaryGate : MonoBehaviour {
    public int requiredMask;
    public GateType gateType;

    private void OnTriggerEnter2D(Collider2D col) {
        var inventory = col.GetComponent<PlayerInventory>();
        if (inventory == null) return;

        bool open = gateType switch {
            GateType.AND => (inventory.playerBits & requiredMask) == requiredMask,
            GateType.OR  => (inventory.playerBits & requiredMask) != 0,
            GateType.XOR => (inventory.playerBits ^ requiredMask) == requiredMask,
            _ => false,
        };

        if (open) GetComponent<Animator>().SetTrigger("Open");
    }
}
```

> *“BinaryGate es un componente autónomo; basta con arrastrarlo a cualquier collider y definir la máscara para crear puertas lógicas sin código adicional.”* — README de Fruit Dash

Este enfoque permite a los equipos insertar mecánicas binarias en cualquier nivel con mínima configuración. Es útil cuando el objetivo es añadir puzzles sin reescribir lógica de interacción. No es adecuado para juegos que requieran física avanzada o interacciones fuera del dominio binario, ya que la máscara se limita a 32 bits y la representación visual de los bits depende de la UI del desarrollador.

## Conclusión  
Fruit Dash demuestra que una mecánica de lógica binaria puede implementarse de forma modular dentro de Unity, ofreciendo a los desarrolladores una plantilla lista para escalar a proyectos más ambiciosos sin inflar la base de código.

**Bottom line:** Fruit Dash convierte la lógica binaria en un bloque reutilizable de Unity, lo que abre la puerta a puzzles más complejos sin sobrecargar el flujo de trabajo de los desarrolladores indie.

---  
**Ver también:** [Fruit Dash: A Solstice Platformer with Binary Code Gates](https://dev.to/agastya_khati_f72c89077c8/fruit-dash-a-solstice-platformer-with-binary-code-gates-2jmi) · [Unity 2022.3 LTS release notes](https://unity.com/releases/editor/2022.3)
