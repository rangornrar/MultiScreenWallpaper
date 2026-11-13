[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Multi-Monitor Wallpaper Generator

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** is a Windows app built with **C# and WinUI 3** for composing, organizing, and applying wallpapers across multiple monitors. Real screen size mode aligns a panorama across displays of different sizes and resolutions.

## 🚀 Key Features

### 🖥️ Advanced Multi-Monitor Management
- **Automatic detection** of your screens' physical layout (left/right, height).
- **Native Implementation**: Applies a different wallpaper per monitor (via the Windows `IDesktopWallpaper` API).
- **Fallback Mode**: Automatically switches to "Span" mode if the API is unsupported.
- **Real screen size** (*Screens* menu): each screen is placed by its physical size (read from EDID, editable) and the gap between panels, so a horizon stays straight across a 27″ and a 24″ display.
- **Automatic wallpaper**: one wallpaper remembered per screen setup, reapplied when screens change (docking) or when Windows restores a theme; image rotation from a folder; notification-area icon and start with Windows.

### 📐 The Absolute Visibility Engine (Fit Inside)
The program adheres to the 100% rule:
- **0 Cropping**: in *Fit* mode, automatic layouts never cut an image's edges; cropping is a manual choice (*Crop* mode).
- **0 Overlap**: No photo covers another photo.
- **0 Overflow**: Images will never spill off the screen edges.
- **0 Distortion**: The original aspect ratio is mathematically preserved.
- **Fill mode (optional)**: covers every screen; each photo is cropped around detected faces (OpenCV), otherwise around its most detailed area. Never distorted.

### 🧩 6 Layout Algorithms (Auto-Layout)
- ⭐ **Maximum Optimization**: searches binary slicing-floorplan trees with a fixed number of tries and a fixed seed: same images, same result. The *Variants…* button shows 4 layouts side by side. Heuristic: no guarantee of a global optimum.
- **Perfect Mosaic**: A randomized patchwork arrangement (BSP technique).
- **Justified Lines**: Alignment similar to Flickr/Google Images.
- **Regular Grid**: A mathematically uniform grid.
- **Vertical Strips** & **Horizontal Strips**: Full height or full width panoramic slicing.

![Maximum Optimization Heuristic](site/assets/screens/desk.webp)

### ⚡ Performance & Editing
- **Preview thumbnails**. The editor uses thumbnails up to 1,024 pixels.
- **Built-in Editing**: Brightness, Contrast, Saturation, Blur, and Rotation.
- **HD Rendering**: The final export leverages the original Ultra HD files for absolute maximum quality.

## Requirements and installation

- **Running the app**. x64 Windows. Windows 11 is recommended. The package declares Windows 10 version 2004 (build 19041) as its technical minimum.
- **Building from source**. x64 Windows, the .NET 10 SDK, and access to NuGet to restore the Windows App SDK and other dependencies.

The MSIX package and self-contained build include the .NET and Windows App SDK runtimes. Python is used only by some repository scripts.

## Get WallCraft Pro

- The MSIX package is intended for the Microsoft Store. The [Microsoft Store guide](docs/MICROSOFT_STORE.md) covers packaging and submission.
- To try the C# development build, download `WallCraft-win-x64` from a successful run of the [C# workflow](https://github.com/rangornrar/MultiScreenWallpaper/actions/workflows/csharp.yml). Extract the entire archive into a folder and run `WallCraft.exe`.

### Build from source

```powershell
dotnet publish csharp/src/WallCraft.App -c Release -r win-x64 -p:Platform=x64 --self-contained true -p:PublishSingleFile=true -o publish/win-x64
```

Run `publish/win-x64/WallCraft.exe`. Keep the other files in that folder alongside the executable.

## 🛠️ Usage

1. Open **WallCraft Pro** from the Start menu after installation, or run `WallCraft.exe` from the build folder.
3. **Language**: choose EN/FR/ES/DE directly from the UI.
4. **Choose a layout**: select one of the 6 modes ("Maximum Optimization" is recommended to limit black bars).
5. **Auto-Arrange**, then fine-tune by hand: *Move*, *Scale* and *Crop* modes, layer forward/back, *Rotate 90°* and *Adjust…* (brightness, contrast, saturation, blur).
6. **File menu**:
    * Save / open a project (`Ctrl+S` / `Ctrl+O`).
    * Export the full image (`Ctrl+E`) or one image per screen.
    * 🖥️ Apply wallpaper: updates your Windows desktop, screen by screen.

## 📂 Repository layout

| Folder | Contents |
|---|---|
| `csharp/` | WinUI 3 app, composition engine, and Windows integration |
| `python/` | Legacy Python/Tkinter implementation kept for migration references |
| `site/` | Website generator, assets, and pages |
| `docs/` | Architecture, tests, and release process |
| `tools/` | Scripts for the website, translations, and reference data |

## 🐛 Troubleshooting

- **Black bars in Fit mode**. Fit keeps each photo whole. Use *Fill* to cover the screens by cropping.
- **Full-size export exceeds the graphics limit**. Export one image per screen when the composition exceeds the GPU’s texture size limit.

## 📄 License

Released under the [MIT License](LICENSE).

## Architecture and validation

[Architecture](docs/ARCHITECTURE.md) · [Tests and validation](docs/QUALITY.md) · [Migration and compatibility](docs/MIGRATION_CSHARP.md).
