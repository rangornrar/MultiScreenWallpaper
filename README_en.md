[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Multi-Monitor Wallpaper Generator

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** is a powerful Python application designed to create, organize, and apply wallpapers across complex multi-monitor setups.

It completely solves the issue of disparate monitor resolutions and borders through its intelligent engine: it merges multiple photos **without ever distorting or cropping them**, guaranteeing **100% absolute visibility** of your images ("Fit Inside" principle).

![WallCraft Interface](assets/wallcraft_app_ui_1773221294829.png)

---

## 🚀 Key Features

### 🖥️ Advanced Multi-Monitor Management
- **Automatic detection** of your screens' physical layout (left/right, height).
- **Native Implementation**: Applies a different wallpaper per monitor (via the Windows `IDesktopWallpaper` API).
- **Fallback Mode**: Automatically switches to "Span" mode if the API is unsupported.

### 📐 The Absolute Visibility Engine (Fit Inside)
The program adheres to the 100% rule:
- **0 Cropping**: No uploaded image will have its edges cut off.
- **0 Overlap**: No photo covers another photo.
- **0 Overflow**: Images will never spill off the screen edges.
- **0 Distortion**: The original aspect ratio is mathematically preserved.

### 🧩 6 Layout Algorithms (Auto-Layout)
- ⭐ **Maximum Optimization (Slow)**: The crown jewel of the app. It simulates hundreds of thousands of geometric permutations via a binary "Slicing Floorplan" tree to nest your images with zero internal empty space, forming a colossal block that statistically reduces black bars to near-zero.
- **Perfect Mosaic**: A randomized patchwork arrangement (BSP technique).
- **Justified Lines**: Alignment similar to Flickr/Google Images.
- **Regular Grid**: A mathematically uniform grid.
- **Vertical Strips** & **Horizontal Strips**: Full height or full width panoramic slicing.

![Maximum Optimization Heuristic](assets/wallcraft_optimal_layout_1773221310533.png)

### ⚡ Performance & Editing
- **Proxy System**: Uses thumbnails for a hyper-fluid UI even with 8K images.
- **Built-in Editing**: Brightness, Contrast, Saturation, Blur, and Rotation.
- **HD Rendering**: The final export leverages the original Ultra HD files for absolute maximum quality.

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher.
- Windows 10/11 (Required for the desktop wallpaper API).

### Dependencies
```bash
pip install pillow screeninfo
```

## 🛠️ Usage
1. Launch the app: `python main.py`
2. **Add Images**: Click the button or drag and drop files.
3. **Language Menu**: Choose EN/FR/ES/DE dynamically directly from the UI.
4. **Choose a Layout**: Select one of the 6 modes ("Maximum Optimization" is recommended for limiting global black bars).
5. **Auto-Arrange**: Click the "🎲" button and let the mathematical engine do the rest.
6. **Apply**:
    * 💾 Export: Save a large composite mockup.
    * ✂ Split: Divide the composition into images mapped to your physical screens.
    * 🖥️ Apply: Actively modify your Windows desktop background.

## 📂 Project Structure
* `main.py`: Entry point, hooks High-DPI Windows settings.
* `ui.py`: Window, interactive canvas, menus and mouse event loop.
* `locales.py`: Multilingual registry string dictionary.
* `image_tools.py`: Core logic. Deep image manipulation and layout engine strategies (`AutoLayoutStrategy`).
* `screen_splitter.py`: `ctypes` system calls for native Windows injection.

## 🐛 Troubleshooting
* **Is the application blurry?** Run it via the standard Windows terminal (cmd/powershell) rather than an IDE terminal to ensure Windows High-DPI handling is engaged.
* **Are black bars visible on the edges?** This is expected behavior. Because the application refuses to ever crop by design, the geometry boxes display a black bar to keep the image 100% visible. The "Maximum Optimization" option allows you to compress these black bars to the absolute possible minimum mathematically.
