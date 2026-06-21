---
title: "Windows 11 22H2 muestra el selector de asociación de archivos"
date: "2026-06-21"
description: "En Windows 11 22H2, al abrir un archivo sin asociación aparece un cuadro que permite elegir una aplicación o buscar en Microsoft Store, sustituyendo error."
tags: ["Dev", "infraestructura", "tendencias"]
cover: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=900&q=80"
source_urls:
  - "https://movq.de/blog/postings/2026-06-20/0/POSTING-en.html"
---

Windows 11 22H2 ya muestra un cuadro de diálogo al hacer clic en un archivo sin asociación — y el cambio ya está en producción. El nuevo picker sustituye el antiguo mensaje de error “No se puede abrir este archivo” y permite elegir una aplicación o buscar en Microsoft Store directamente desde la ventana emergente. La actualización se documentó en el blog de Movq el 20 de junio 2026, y ya está habilitada para los usuarios de Windows 11 versión 22631.3639 y posteriores.

## Qué es y qué ha pasado
El comportamiento forma parte de la evolución de la interfaz de usuario de Windows para la gestión de tipos de archivo. Hasta Windows 10, al intentar abrir un archivo sin extensión conocida o sin programa registrado, el sistema mostraba un mensaje estático y requería que el usuario navegara manualmente a “Abrir con…”. Con la actualización 22H2, Microsoft introdujo un componente de UI llamado **File‑Association Picker** que se activa automáticamente cuando la llamada a `ShellExecuteEx` no encuentra una aplicación asociada.

El picker no es un proyecto de código abierto; es una pieza interna del shell de Windows escrita en C++/WinRT y expuesta a través de la API `IFileOpenDialog`. Su lógica decide, en función de la categoría del archivo y de la disponibilidad en Microsoft Store, si muestra una lista de aplicaciones instaladas, sugiere descargas o permite buscar en la web. La diferencia con la solución anterior radica en la integración directa con la tienda y la posibilidad de registrar asociaciones temporales sin tocar el registro de Windows.

## Por qué importa ahora
Desde hace años, la fragmentación de asociaciones de archivo ha sido una fuente de fricción para administradores de sistemas y usuarios avanzados. En entornos corporativos, los scripts de despliegue suelen depender de asociaciones predefinidas; la ausencia de una aplicación válida suele provocar fallos silenciosos en pipelines de CI/CD. La llegada del picker cierra esa brecha al ofrecer una ruta explícita para resolver la asociación, reduciendo la necesidad de intervención manual.

El cambio coincide con la tendencia de Microsoft a consolidar la experiencia de usuario alrededor de la **Microsoft Store** como hub de aplicaciones, similar a lo que Apple ha hecho con su App Store en macOS. Además, la nueva UI se alinea con la estrategia de **Windows App SDK** (versión 1.4), que promueve la declaratividad de capacidades y la detección automática de tipos de contenido. Proyectos como **WinGet** y **wingetui** ya integran lógica para instalar paquetes cuando una asociación falta; ahora el propio SO puede iniciar ese proceso sin depender de scripts externos.

## Detalles técnicos y qué significa para ti
El picker se invoca cuando `ShellExecuteEx` devuelve `ERROR_NO_ASSOCIATION`. Internamente, el shell lanza `IFileOpenDialog::SetOptions(FOS_PICKER)`, que abre la UI con los siguientes parámetros relevantes:

```cpp
IFileOpenDialog *dlg = nullptr;
CoCreateInstance(CLSID_FileOpenDialog, nullptr, CLSCTX_INPROC_SERVER,
                 IID_PPV_ARGS(&dlg));
DWORD options;
dlg->GetOptions(&options);
options |= FOS_PICKER;
dlg->SetOptions(options);
dlg->Show(nullptr);
```

> *“When no default handler is found, the File‑Association Picker is presented, offering installed apps, store recommendations, and a search interface.”* — Microsoft Windows Shell release notes, 22H2.

En la práctica, el picker es útil para desarrolladores que distribuyen herramientas de línea de comandos sin instalador tradicional; al empaquetar el binario con una extensión registrada en el instalador, el usuario podrá abrir directamente el ejecutable desde el Explorador. No es recomendable usarlo en entornos críticos donde la instalación automática de software está deshabilitada por políticas de grupo, ya que la UI puede intentar abrir Microsoft Store, lo que provocaría errores de permisos.

## Cierre
**Bottom line:** La introducción del File‑Association Picker en Windows 11 elimina el punto ciego de los archivos sin asociación, integrando la selección de aplicaciones y la tienda en una única experiencia de usuario.

---  
**Ver también:** [Windows UI evolution: Clicking an unassociated file](https://movq.de/blog/postings/2026-06-20/0/POSTING-en.html) · [Microsoft Store integration guide](https://learn.microsoft.com/windows/apps/desktop/desktop-to-uwp/desktop-to-uwp-overview)
