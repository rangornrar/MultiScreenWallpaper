[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Generador de Fondos de Pantalla Multimonitor

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** es una aplicación de Windows desarrollada con **C# y WinUI 3** para componer, organizar y aplicar fondos de pantalla en varios monitores. El modo Tamaño real alinea una panorámica entre pantallas de distintos tamaños y resoluciones.

## 🚀 Características Clave

### 🖥️ Gestión Avanzada Multimonitor
- **Detección automática** de la disposición física de sus pantallas (izquierda/derecha, altura).
- **Implementación Nativa**: Aplica un fondo de pantalla diferente por monitor (a través de la API `IDesktopWallpaper` de Windows).
- **Modo de Respaldo**: Cambia automáticamente al modo "Panorámica" si la API nativa no es compatible.
- **Tamaño real de las pantallas** (menú *Pantallas*): cada pantalla se coloca según su tamaño físico (leído del EDID, modificable) y el espacio entre paneles; un horizonte sigue recto entre un monitor de 27″ y otro de 24″.
- **Fondo automático**: un fondo guardado por configuración de pantallas, aplicado de nuevo cuando cambian las pantallas (base de conexión) o Windows restaura un tema; rotación de imágenes de una carpeta; icono en el área de notificación e inicio con Windows.

### 📐 El Motor de Visibilidad Absoluta
El programa se adhiere a la regla del 100%:
- **0 Recortes (Crop)**: en modo *Ajustar*, los modos automáticos nunca cortan los bordes de una imagen; el recorte es una elección manual (modo *Recortar*).
- **0 Superposición**: Ninguna foto cubre a otra foto.
- **0 Desbordamiento**: Las imágenes nunca superarán los bordes de la pantalla.
- **0 Distorsión**: La relación de aspecto original se conserva matemáticamente.
- **Modo Rellenar (opcional)**: cubre todas las pantallas; cada foto se recorta alrededor de las caras detectadas (OpenCV) o de su zona con más detalle. Nunca se deforma.

### 🧩 6 Algoritmos de Disposición (Auto-Layout)
- ⭐ **Optimización Máxima**: búsqueda en árboles de corte binarios con un número de intentos y una semilla fijos: mismas imágenes, mismo resultado. El botón *Variantes…* muestra 4 disposiciones lado a lado. Heurística: sin garantía de óptimo global.
- **Mosaico Perfecto**: Un arreglo aleatorio tipo patchwork (Técnica BSP).
- **Líneas Justificadas**: Alineación similar a Flickr o Google Images.
- **Cuadrícula Regular**: Una cuadrícula matemáticamente uniforme.
- **Bandas Verticales** y **Bandas Horizontales**: Rebanado panorámico de altura o anchura completa.

![Heurística de Optimización Máxima](site/assets/screens/desk.webp)

### ⚡ Rendimiento y Edición
- **Miniaturas de vista previa**. El editor usa miniaturas de hasta 1024 píxeles.
- **Edición Integrada**: Brillo, Contraste, Saturación, Desenfoque y Rotación.
- **Renderizado HD**: La exportación final aprovecha los archivos originales Ultra HD para máxima calidad absoluta.

## Requisitos e instalación

- **Uso de la aplicación**. Windows x64. Se recomienda Windows 11. El paquete declara Windows 10 versión 2004 (compilación 19041) como mínimo técnico.
- **Compilación**. Windows x64, SDK de .NET 10 y acceso a NuGet para restaurar el Windows App SDK y las demás dependencias.

El paquete MSIX y la compilación autónoma incluyen los entornos de ejecución de .NET y Windows App SDK. Python se usa solo en algunos scripts del repositorio.

## Obtener WallCraft Pro

- El paquete MSIX está destinado a Microsoft Store. La [guía de Microsoft Store](docs/MICROSOFT_STORE.md) explica cómo preparar y enviar el paquete.
- Para probar la compilación de desarrollo en C#, descargue `WallCraft-win-x64` de una ejecución correcta del [flujo de trabajo de C#](https://github.com/rangornrar/MultiScreenWallpaper/actions/workflows/csharp.yml). Extraiga todo el archivo en una carpeta y ejecute `WallCraft.exe`.

### Compilar desde el código fuente

```powershell
dotnet publish csharp/src/WallCraft.App -c Release -r win-x64 -p:Platform=x64 --self-contained true -p:PublishSingleFile=true -o publish/win-x64
```

Ejecute `publish/win-x64/WallCraft.exe`. Conserve junto al ejecutable los demás archivos de esa carpeta.

## 🛠️ Uso

1. Abra **WallCraft Pro** desde el menú Inicio tras instalarlo, o ejecute `WallCraft.exe` desde la carpeta de compilación.
3. **Idioma**: elija EN/FR/ES/DE directamente desde la interfaz.
4. **Elija una disposición**: seleccione uno de los 6 modos («Optimización Máxima» recomendada para limitar las bandas negras).
5. **Auto-Organizar** y luego ajuste a mano: modos *Mover*, *Escalar* y *Recortar*, capas adelante/atrás, *Girar 90°* y *Ajustes…* (brillo, contraste, saturación, desenfoque).
6. **Menú Archivo**:
    * Guardar / abrir un proyecto (`Ctrl+S` / `Ctrl+O`).
    * Exportar la imagen completa (`Ctrl+E`) o una imagen por pantalla.
    * 🖥️ Aplicar fondo: modifica su escritorio de Windows, pantalla por pantalla.

## 📂 Organización del repositorio

| Carpeta | Contenido |
|---|---|
| `csharp/` | Aplicación WinUI 3, motor de composición e integración con Windows |
| `python/` | Implementación anterior en Python/Tkinter, conservada como referencia para la migración |
| `site/` | Generador, recursos y páginas del sitio web |
| `docs/` | Arquitectura, pruebas y publicación |
| `tools/` | Scripts del sitio web, traducciones y datos de referencia |

## 🐛 Solución de problemas

- **Bandas negras en el modo Ajustar**. Este modo conserva las fotos completas. Use *Rellenar* para cubrir las pantallas mediante recorte.
- **La exportación completa supera el límite gráfico**. Exporte una imagen por pantalla si la composición supera el tamaño máximo de textura de la GPU.

## 📄 Licencia

Distribuido bajo la [licencia MIT](LICENSE).

## Arquitectura y validación

[Arquitectura](docs/ARCHITECTURE.md) · [Pruebas y validación](docs/QUALITY.md) · [Migración y compatibilidad](docs/MIGRATION_CSHARP.md).
