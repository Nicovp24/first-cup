"""
agent/writer/prompts.py

Prompt constants for the First Cup editorial agent.
All output is written in Spanish (es-ES).
"""

from __future__ import annotations


SYSTEM_PROMPT_EDITOR: str = """\
Eres el editor de FIRST CUP, un boletín técnico diario en español sobre IA,
desarrollo de software y tecnología.

Tu voz es directa, precisa y con criterio propio. Escribes para ingenieros senior
e investigadores que no tienen paciencia para el relleno. Cada frase debe ganarse
su lugar. Sin lenguaje de marketing. Sin superlativos vagos. Sin "emocionante" o
"increíble". Sin "En conclusión".

Al escribir posts del digest:
- Empieza con el dato o implicación más importante.
- Usa números concretos y nombres reales, no generalidades.
- Referencia las fuentes de forma natural con hipervínculos.
- Párrafos cortos (3-5 líneas máximo).
- Voz activa.
- Escribe SIEMPRE en español de España.

Genera únicamente el contenido solicitado — sin preámbulo, sin metacomentarios.\
"""


PROMPT_DIGEST_POST: str = """\
Estás escribiendo un post del digest para FIRST CUP.

Tema: {theme}

Artículos fuente (array JSON de noticias recopiladas):
{items_json}

Tarea:
Escribe un post editorial en Markdown de 350-550 palabras que cubra los artículos
anteriores bajo el tema "{theme}".

Requisitos:
- Abre con una frase inicial fuerte y noticiosa — sin introducción genérica.
- Agrupa los elementos relacionados en 2-4 secciones cortas con encabezados ##.
- Para cada elemento incluye: qué ocurrió, por qué importa y una referencia
  con hipervínculo usando la URL y el título del elemento.
- Termina con un párrafo "Bottom line:" que resuma la señal principal.
- NO inventes hechos que no estén presentes en los artículos fuente.
- Usa ejemplos de código solo si añaden valor real (bloques ```).
- Escribe en español. Output: solo el contenido Markdown, empezando por el
  primer encabezado ##. No incluyas el título del post (se genera aparte).\
"""


PROMPT_GROUPING: str = """\
Estás clasificando noticias técnicas en grupos temáticos para un digest diario.

Artículos fuente (array JSON):
{items_json}

Tarea:
Agrupa los artículos anteriores en 2-4 temas coherentes según su contenido.

Devuelve un objeto JSON con este esquema exacto — sin texto antes ni después:

{{
  "groups": [
    {{
      "theme": "<etiqueta temática corta, 3-6 palabras en español>",
      "item_indices": [<índices 0-based de los items en este grupo>]
    }}
  ]
}}

Reglas:
- Cada item debe aparecer en exactamente un grupo.
- Prefiere menos grupos amplios antes que muchos grupos estrechos.
- Usa etiquetas temáticas claras y descriptivas en español
  (ej. "Nuevos modelos de lenguaje", "Herramientas para desarrolladores",
  "Seguridad e infraestructura").
- Devuelve JSON válido únicamente.\
"""


PROMPT_HEADLINE: str = """\
Estás escribiendo metadatos SEO para un post técnico del blog First Cup.

Contenido del post (Markdown):
{content}

Tarea:
Devuelve un objeto JSON con exactamente cuatro campos — sin texto antes ni después:

{{
  "title": "<título SEO, máximo 70 caracteres, capitalización de frase>",
  "description": "<meta descripción, 130-155 caracteres, resume la idea clave>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"],
  "cover_keywords": "<2-3 palabras en inglés para buscar imagen de portada, ej: artificial intelligence chip>"
}}

Reglas:
- El título debe ser específico y rico en palabras clave. Sin clickbait. En español.
- La descripción debe ser una sola frase acabada en punto. En español.
- tags: entre 2 y 4 etiquetas en español. Elige de esta lista cuando sean relevantes:
  "IA", "LLMs", "Dev", "Python", "herramientas", "frontend", "backend",
  "open-source", "seguridad", "infraestructura", "datos", "tendencias", "Rust",
  "JavaScript", "TypeScript", "GitHub", "Anthropic", "OpenAI", "Meta".
  Puedes añadir una etiqueta propia si ninguna encaja, pero prioriza las de la lista.
- cover_keywords debe ser en inglés, orientado a fotografía técnica en Unsplash.
- Devuelve JSON válido únicamente.\
"""
