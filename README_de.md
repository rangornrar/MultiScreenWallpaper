[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D21VSKW5)

# 🎨 WallCraft Pro - Multi-Monitor-Hintergrundbild-Generator

🌍 **[English](README_en.md)** | **[Français](README.md)** | **[Español](README_es.md)** | **[Deutsch](README_de.md)**

**WallCraft Pro** ist eine Windows-Anwendung mit **C# und WinUI 3**, die Hintergrundbilder für mehrere Monitore gestaltet, organisiert und anwendet. Der Modus für reale Bildschirmgrößen richtet ein Panorama über Monitore mit unterschiedlichen Größen und Auflösungen aus.

## 🚀 Hauptfunktionen

### 🖥️ Erweitertes Multi-Monitor-Management
- **Automatische Erkennung** der physischen Anordnung Ihrer Bildschirme (links/rechts, Höhe).
- **Native Implementierung**: Setzt pro Monitor ein anderes Hintergrundbild (über die Windows `IDesktopWallpaper`-API).
- **Fallback-Modus**: Wechselt automatisch in den "Panorama"-Modus (Span), falls die native API nicht unterstützt wird.
- **Reale Bildschirmgröße** (Menü *Bildschirme*): Jeder Bildschirm wird nach seiner physischen Größe (aus der EDID, anpassbar) und dem Abstand zwischen den Panels platziert; ein Horizont bleibt zwischen einem 27″- und einem 24″-Monitor gerade.
- **Automatisches Hintergrundbild**: ein gespeichertes Hintergrundbild pro Bildschirmkonfiguration, erneut angewendet, wenn sich die Bildschirme ändern (Dockingstation) oder Windows ein Design wiederherstellt; Bildwechsel aus einem Ordner; Symbol im Infobereich und Start mit Windows.

### 📐 Die Absolute "Fit Inside" Engine
Das Programm hält sich strikt an die 100 % Regel:
- **0 Zuschnitt (Crop)**: Im Modus *Einpassen* schneiden die automatischen Layouts nie Bildränder ab; Zuschneiden ist eine manuelle Entscheidung (Modus *Zuschneiden*).
- **0 Überlappung**: Kein Foto verdeckt ein anderes Foto.
- **0 Überstand**: Bilder ragen niemals über die Bildschirmränder hinaus.
- **0 Verzerrung**: Das ursprüngliche Seitenverhältnis bleibt mathematisch gewahrt.
- **Modus Füllen (optional)**: bedeckt alle Bildschirme; jedes Foto wird um erkannte Gesichter (OpenCV) zugeschnitten, sonst um seinen detailreichsten Bereich. Nie verzerrt.

### 🧩 6 Layout-Algorithmen (Auto-Layout)
- ⭐ **Maximale Optimierung**: Suche über binäre Slicing-Floorplan-Bäume mit fester Anzahl an Versuchen und festem Startwert: gleiche Bilder, gleiches Ergebnis. Die Schaltfläche *Varianten…* zeigt 4 Layouts nebeneinander. Heuristik: kein garantiertes globales Optimum.
- **Perfektes Mosaik**: Eine randomisierte Patchwork-Anordnung (BSP-Technik).
- **Ausgerichtete Linien**: Ausrichtung ähnlich wie bei Flickr/Google Bilder.
- **Regelmäßiges Raster**: Ein mathematisch gleichmäßiges Raster.
- **Vertikale & Horizontale Streifen**: Panorama-Slicing über die volle Höhe oder volle Breite.

![Maximale Optimierungsheuristik](site/assets/screens/desk.webp)

### ⚡ Leistung & Bearbeitung
- **Vorschaubilder**. Der Editor verwendet Vorschaubilder mit bis zu 1.024 Pixeln.
- **Integrierte Bildbearbeitung**: Helligkeit, Kontrast, Sättigung, Unschärfe und Drehung.
- **HD-Rendering**: Der endgültige Export verwendet die originalen Ultra-HD-Dateien für absolut maximale Qualität.

## Voraussetzungen und Installation

- **Nutzung**. Windows x64. Windows 11 wird empfohlen. Das Paket setzt technisch mindestens Windows 10, Version 2004 (Build 19041), voraus.
- **Kompilierung**. Windows x64, das .NET-10-SDK und Zugriff auf NuGet für das Windows App SDK und die weiteren Abhängigkeiten.

Das MSIX-Paket und der eigenständige Build enthalten die Laufzeitkomponenten für .NET und das Windows App SDK. Python wird nur für einige Skripte im Repository verwendet.

## WallCraft Pro beziehen

- Das MSIX-Paket ist für den Microsoft Store vorgesehen. Die [Anleitung zum Microsoft Store](docs/MICROSOFT_STORE.md) beschreibt die Vorbereitung und Einreichung.
- Um den C#-Entwicklungsbuild auszuprobieren, laden Sie `WallCraft-win-x64` aus einem erfolgreichen Lauf des [C#-Workflows](https://github.com/rangornrar/MultiScreenWallpaper/actions/workflows/csharp.yml) herunter. Entpacken Sie das gesamte Archiv in einen Ordner und starten Sie `WallCraft.exe`.

### Aus dem Quellcode erstellen

```powershell
dotnet publish csharp/src/WallCraft.App -c Release -r win-x64 -p:Platform=x64 --self-contained true -p:PublishSingleFile=true -o publish/win-x64
```

Starten Sie `publish/win-x64/WallCraft.exe`. Lassen Sie die übrigen Dateien im selben Ordner.

## 🛠️ Verwendung

1. Öffnen Sie **WallCraft Pro** nach der Installation im Startmenü oder starten Sie `WallCraft.exe` im Ausgabeordner.
3. **Sprache**: Wählen Sie EN/FR/ES/DE direkt in der Oberfläche.
4. **Layout wählen**: Wählen Sie einen der 6 Modi („Maximale Optimierung“ empfohlen, um schwarze Balken zu minimieren).
5. **Auto-Anordnen**, dann von Hand verfeinern: Modi *Bewegen*, *Skalieren* und *Zuschneiden*, Ebenen vor/zurück, *90° drehen* und *Anpassen…* (Helligkeit, Kontrast, Sättigung, Unschärfe).
6. **Menü Datei**:
    * Projekt speichern / öffnen (`Strg+S` / `Strg+O`).
    * Gesamtbild exportieren (`Strg+E`) oder ein Bild pro Bildschirm.
    * 🖥️ Hintergrundbild anwenden: ändert Ihren Windows-Desktop, Bildschirm für Bildschirm.

## 📂 Aufbau des Repositorys

| Ordner | Inhalt |
|---|---|
| `csharp/` | WinUI-3-Anwendung, Kompositionslogik und Windows-Integration |
| `python/` | Frühere Python/Tkinter-Implementierung als Referenz für die Migration |
| `site/` | Generator, Ressourcen und Seiten der Website |
| `docs/` | Architektur, Tests und Veröffentlichung |
| `tools/` | Skripte für Website, Übersetzungen und Referenzdaten |

## 🐛 Fehlerbehebung

- **Schwarze Balken im Modus Einpassen**. Dieser Modus erhält die Fotos vollständig. Mit *Füllen* werden die Fotos zugeschnitten, um die Bildschirme auszufüllen.
- **Das Gesamtbild überschreitet das Grafiklimit**. Exportieren Sie ein Bild pro Monitor, wenn die Komposition die maximale Texturgröße der GPU überschreitet.

## 📄 Lizenz

Veröffentlicht unter der [MIT-Lizenz](LICENSE).

## Architektur und Validierung

[Architektur](docs/ARCHITECTURE.md) · [Tests und Validierung](docs/QUALITY.md) · [Migration und Kompatibilität](docs/MIGRATION_CSHARP.md).
