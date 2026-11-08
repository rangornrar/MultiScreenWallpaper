[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Generador de Fondos de Pantalla Multimonitor

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** es una potente aplicación de Python diseñada para crear, organizar y aplicar fondos de pantalla en configuraciones complejas de múltiples monitores.

Resuelve completamente el problema de las resoluciones de monitores dispares mediante su motor inteligente: permite fusionar múltiples fotos **sin distorsionarlas ni recortarlas nunca**, garantizando una **visibilidad absoluta del 100%** de sus imágenes (principio "Encuadre exacto" / Fit Inside).

![Interfaz de WallCraft](assets/wallcraft_app_ui_1773221294829.png)

---

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

![Heurística de Optimización Máxima](assets/wallcraft_optimal_layout_1773221310533.png)

### ⚡ Rendimiento y Edición
- **Sistema de Proxy**: Utiliza miniaturas para una interfaz de usuario extremadamente fluida incluso con imágenes 8K.
- **Edición Integrada**: Brillo, Contraste, Saturación, Desenfoque y Rotación.
- **Renderizado HD**: La exportación final aprovecha los archivos originales Ultra HD para máxima calidad absoluta.

---

## 📦 Instalación

### Requisitos previos
- Python 3.10 o superior.
- Windows 10/11 (Requerido debido a la API de fondos de pantalla).

### Dependencias
```bash
pip install pillow screeninfo
```

## 📥 Descargar
El ejecutable de Windows se publica en la página [GitHub Releases](https://github.com/rangornrar/MultiScreenWallpaper/releases/latest). Su huella SHA-256 figura en las notas de cada versión.

## 🛠️ Uso
1. Inicie la aplicación: `python main.py` (o el ejecutable de la [última versión](https://github.com/rangornrar/MultiScreenWallpaper/releases/latest)).
2. **Añadir imágenes**: botón «+ Añadir Imágenes» o menú *Archivo*. Las fotos de smartphone se enderezan automáticamente.
3. **Idioma**: elija EN/FR/ES/DE directamente desde la interfaz.
4. **Elija una disposición**: seleccione uno de los 6 modos («Optimización Máxima» recomendada para limitar las bandas negras).
5. **Auto-Organizar** y luego ajuste a mano: modos *Mover*, *Escalar* y *Recortar*, capas adelante/atrás, *Girar 90°* y *Ajustes…* (brillo, contraste, saturación, desenfoque).
6. **Menú Archivo**:
    * Guardar / abrir un proyecto (`Ctrl+S` / `Ctrl+O`).
    * Exportar la imagen completa (`Ctrl+E`) o una imagen por pantalla.
    * 🖥️ Aplicar fondo: modifica su escritorio de Windows, pantalla por pantalla.

## 📂 Estructura del Proyecto
* `main.py`: Punto de entrada, gestiona el High-DPI de Windows.
* `ui.py`: Ventana, lienzo interactivo y bucle de eventos.
* `locales.py`: Diccionario multilingüe de cadenas.
* `image_tools.py`: Lógica principal, matemáticas y diseño.
* `screen_splitter.py`: Llamadas `ctypes` a Windows.

## 🐛 Solución de Problemas
* **¿La aplicación se ve borrosa?** Ejecútela a través de la terminal estándar (cmd/powershell) en lugar de la IDE para garantizar que Windows utilice la alta fidelidad visual nativa.
* **¿Bandas negras visibles?** En modo *Ajustar* es lo esperado: ninguna imagen se recorta y el espacio restante queda negro. Elija *Rellenar* para cubrir las pantallas, u «Optimización Máxima» para reducir las bandas.


## 📄 Licencia
Distribuido bajo la [licencia MIT](LICENSE).

## Architecture & validation

[Architecture and trade-offs](docs/ARCHITECTURE.md) · [Quality and test scope](docs/QUALITY.md).
