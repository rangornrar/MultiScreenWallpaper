from pathlib import Path
import json
import posixpath
import shutil
from html import escape

TODAY = "2026-11-13"
BASE_URL = "https://wallcraft.archi-it.fr/"
PROJECT_BASE_URL = BASE_URL.removesuffix("html/")
REPO_URL = "https://github.com/rangornrar/MultiScreenWallpaper"
RELEASES_URL = f"{REPO_URL}/releases"
ARCHI_IT_URL = "https://www.archi-it.fr/#labs"
ARCHI_IT_HOME_URL = "https://www.archi-it.fr/"
PRODUCT_VERSION = "2026.11.13"
# Tag de la release GitHub qui contient l'exécutable (le workflow release.yml le nomme
# WallCraft-Pro-v<version>-Windows.exe). À mettre à jour avec PRODUCT_VERSION.
RELEASE_TAG = "Tag_v2026.11.13"
DOWNLOAD_URL = f"{REPO_URL}/releases/download/{RELEASE_TAG}/WallCraft-Pro-v{PRODUCT_VERSION}-Windows.exe"
GOOGLE_SITE_VERIFICATION = ""
# Anciennes captures (2026.3) : ces noms ne servent plus qu'à les remplacer par les captures par langue
# de site/assets/screens (voir apply_2026_11 et tools/make_screenshots.py).
SCREEN_1 = "assets/wallcraft_2026_workspace.png"
SCREEN_2 = "assets/wallcraft_2026_clean_output.png"
SCREEN_3 = "assets/wallcraft_2026_workspace_stage.png"

CSS_CONTENT = """
:root {
    --bg: #0b0e14;
    --panel: #161b22;
    --border: rgba(255, 255, 255, 0.1);
    --text: #c9d1d9;
    --text-dim: #8b949e;
    --accent: #58a6ff;
    --accent-hover: #1f6feb;
    --glass: rgba(22, 27, 34, 0.7);
    --font: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    line-height: 1.6;
    overflow-x: hidden;
}

a { color: var(--accent); text-decoration: none; transition: color 0.2s; }
a:hover { color: var(--accent-hover); }

.button {
    display: inline-block;
    padding: 12px 24px;
    background: var(--accent);
    color: #fff;
    border-radius: 6px;
    font-weight: 600;
    transition: transform 0.2s, background 0.2s;
    cursor: pointer;
    border: none;
}
.button:hover {
    background: var(--accent-hover);
    transform: translateY(-2px);
    color: #fff;
}
.button.secondary {
    background: var(--panel);
    border: 1px solid var(--border);
}
.button.small { padding: 8px 16px; font-size: 0.9em; }

.topbar {
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--glass);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    padding: 16px 0;
}
.topbar-inner {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.topbar-inner { gap: 16px; }
.logo { font-size: 1.4em; font-weight: 800; color: #fff; white-space: nowrap; }
.logo span { color: var(--accent); }
.nav { display: flex; gap: 18px; }
.nav a { color: var(--text-dim); font-size: 0.92em; white-space: nowrap; }
.nav-actions { display: flex; gap: 8px; white-space: nowrap; }
.nav a:hover, .nav a.active { color: var(--accent); }

.hero {
    padding: 48px 20px 40px;
    max-width: 1100px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr);
    column-gap: 48px;
    row-gap: 28px;
    align-items: center;
}
.hero.no-image { grid-template-columns: minmax(0, 760px); padding-bottom: 16px; }
.hero-head { grid-column: 1 / -1; }
.hero-head h1 { font-size: clamp(1.6em, 2.6vw, 2.1em); line-height: 1.2; color: #fff; font-weight: 800; margin-top: 14px; }
.hero-content .lead { font-size: 1.08em; color: var(--text-dim); margin-bottom: 24px; }
.hero-actions { display: flex; gap: 16px; flex-wrap: wrap; }

.section { padding: 52px 20px; max-width: 1100px; margin: 0 auto; }
.section-head { margin-bottom: 28px; max-width: 700px; }
.section-head h2 { font-size: 1.65em; line-height: 1.25; color: #fff; margin-bottom: 10px; }
.section-head p { font-size: 1.02em; color: var(--text-dim); }

.card-grid, .step-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
}
.card {
    background: var(--panel);
    border: 1px solid var(--border);
    padding: 32px;
    border-radius: 12px;
    transition: border-color 0.2s, transform 0.2s;
}
.card:hover { border-color: var(--accent); transform: translateY(-4px); }
.card h3 { color: #fff; margin-bottom: 10px; font-size: 1.12em; }
.card p { color: var(--text-dim); }
.card .meta { margin-top: 24px; font-weight: 600; }

.mini-badge {
    display: inline-block;
    padding: 4px 12px;
    background: rgba(88, 166, 255, 0.1);
    color: var(--accent);
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 600;
    margin-bottom: 16px;
    border: 1px solid rgba(88, 166, 255, 0.2);
}

.feature-list { list-style: none; margin-bottom: 32px; }
.feature-list li { position: relative; padding-left: 28px; margin-bottom: 12px; color: var(--text-dim); }
.feature-list li::before {
    content: "✓";
    position: absolute;
    left: 0;
    color: var(--accent);
    font-weight: bold;
}

.screen-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
}
.screen-card img { width: 100%; height: auto; display: block; }
.article-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: 24px; align-items: start; }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 28px; }
.prose p { margin-bottom: 14px; color: var(--text); }
.prose .feature-list { margin: 16px 0 0; }
.note-box { background: rgba(88, 166, 255, 0.08); border: 1px solid rgba(88, 166, 255, 0.3); border-radius: 12px; padding: 24px; }
.note-box h3 { color: #fff; margin-bottom: 8px; font-size: 1.05em; }
.note-box p { color: var(--text-dim); margin-bottom: 8px; }
.feature-grid.wide { grid-template-columns: 1fr; }
.feature-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 32px; align-items: start; }
.feature-grid .prose p, .feature-grid .prose li { color: var(--text); }
.feature-shot { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
.feature-shot img { display: block; max-width: 100%; height: auto; margin: 0 auto; }
.help-toc { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.help-toc a { border: 1px solid var(--border); border-radius: 999px; padding: 6px 14px; font-size: 0.9em; }
section[id] { scroll-margin-top: 90px; }
.shot-caption { padding: 20px; background: rgba(0,0,0,0.2); border-top: 1px solid var(--border); }
.shot-caption strong { display: block; color: #fff; margin-bottom: 4px; }
.shot-caption p { font-size: 0.9em; color: var(--text-dim); }

.faq-item {
    background: var(--panel);
    border: 1px solid var(--border);
    margin-bottom: 12px;
    border-radius: 8px;
    overflow: hidden;
}
.faq-item summary { padding: 20px; cursor: pointer; font-weight: 600; color: #fff; list-style: none; }
.faq-item .answer { padding: 0 20px 20px; color: var(--text-dim); }

.footer {
    background: #0d1117;
    border-top: 1px solid var(--border);
    padding: 80px 20px 40px;
    margin-top: 80px;
}
.footer-grid {
    max-width: 1100px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 60px;
}
.footer-col h3 { color: #fff; margin-bottom: 24px; font-size: 1.25em; }
.footer-col p { color: var(--text-dim); margin-bottom: 20px; }
.footer-links { list-style: none; }
.footer-links li { margin-bottom: 12px; }
.footer-links a { color: var(--text-dim); }
.footer-links a:hover { color: var(--accent); }
.footer-bottom {
    max-width: 1100px;
    margin: 60px auto 0;
    padding-top: 40px;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--text-dim);
    font-size: 0.9em;
}

.lang-selector { display: flex; gap: 12px; margin-top: 20px; }
.lang-selector a {
    padding: 4px 8px;
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 0.8em;
    color: var(--text-dim);
}
.lang-selector a.active { background: var(--accent); color: #fff; border-color: var(--accent); }

.compare-wrap { overflow-x: auto; margin-bottom: 32px; border: 1px solid var(--border); border-radius: 12px; }
.compare-table { width: 100%; border-collapse: collapse; background: var(--panel); }
.compare-table th { background: rgba(255,255,255,0.05); text-align: left; padding: 16px; color: #fff; border-bottom: 1px solid var(--border); }
.compare-table td { padding: 16px; border-bottom: 1px solid var(--border); color: var(--text-dim); }
.compare-table tr:last-child td { border-bottom: none; }

.highlight-panel {
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    border: 1px solid var(--accent);
    padding: 60px;
    border-radius: 24px;
    text-align: center;
}
.highlight-panel h2 { font-size: 1.7em; color: #fff; margin-bottom: 16px; }

@media (max-width: 900px) {
    .hero { grid-template-columns: 1fr; text-align: center; padding: 40px 20px; }
    .hero-head h1 { font-size: 1.55em; }
    .section-head h2 { font-size: 1.4em; }
    .hero-actions { justify-content: center; }
    .footer-grid { grid-template-columns: 1fr; gap: 40px; }
    .feature-grid, .article-grid { grid-template-columns: 1fr; }
    .nav, .nav-actions .button.secondary { display: none; }
}
"""

JS_CONTENT = """
document.addEventListener('DOMContentLoaded', () => {
    // Basic lang persistence if needed
    const currentLang = document.documentElement.lang;
    const langLinks = document.querySelectorAll('[data-lang-link]');
    
    langLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const targetLang = link.getAttribute('data-lang-link');
            console.log('Switching to', targetLang);
        });
    });
});
"""

# Dossier site/ du dépôt : assets/ (captures) en entrée, html/ (le site à publier sur l'hébergeur) en sortie.
ROOT = Path(__file__).resolve().parent
HTML_ROOT = ROOT / "html"

SLUGS = {
    "home": "",
    "download": "download",
    "how-it-works": "how-it-works",
    "dual-monitor-wallpaper-windows-11": "dual-monitor-wallpaper-windows-11",
    "faq": "faq",
    "compare": "compare",
    "use-cases": "use-cases",
    "dual-monitor-wallpaper-without-cropping": "dual-monitor-wallpaper-without-cropping",
    "mixed-monitor-wallpaper-setup": "mixed-monitor-wallpaper-setup",
    "help": "help",
}

NAV_ORDER = ["download", "how-it-works", "help", "use-cases", "faq", "compare"]
FOOTER_ORDER = ["download", "how-it-works", "help", "faq", "compare", "dual-monitor-wallpaper-without-cropping", "mixed-monitor-wallpaper-setup"]
LANG_ORDER = ["fr", "en", "es", "de"]

LANGS = {
    "en": {
        "name": "English",
        "locale": "en_US",
        "tagline": "Open-source multi-monitor wallpaper studio",
        "skip": "Skip to content",
        "support": "Support on Ko-fi",
        "nav": {
            "home": "Home",
            "download": "Download",
            "how-it-works": "How it works",
            "dual-monitor-wallpaper-windows-11": "Dual monitor",
            "faq": "FAQ",
            "compare": "Compare",
            "use-cases": "Use cases",
            "dual-monitor-wallpaper-without-cropping": "No crop guide",
            "mixed-monitor-wallpaper-setup": "Mixed monitors",
        },
        "footer_about_title": "WallCraft Pro",
        "footer_about_text": "Open-source Windows app for building, splitting, and applying wallpapers across uneven monitor setups without cropping or distortion. Built as part of Archi-IT Labs.",
        "footer_resources_title": "Pages",
        "footer_source_title": "Project",
        "footer_source_text": f"The source code is public on GitHub, and the current packaged Windows release is now available through GitHub Releases as v{PRODUCT_VERSION}.",
        "footer_hub_label": "Open Archi-IT Labs",
        "download_now": f"Download v{PRODUCT_VERSION} for Windows",
        "view_source": "View on GitHub",
        "view_releases": "Open GitHub releases",
        "learn_more": "Learn how it works",
        "related_title": "Keep exploring",
        "ready_title": "Ready to build a wallpaper that actually fits your setup?",
        "ready_text": "Download the current build, test your monitor layout, and keep the GitHub repository nearby for updates and source code.",
        "read_page": "Read page",
        "updated": "Updated",
    },
    "fr": {
        "name": "Français",
        "locale": "fr_FR",
        "tagline": "Studio open source de fonds d'écran multi-écrans",
        "skip": "Aller au contenu",
        "support": "Me soutenir sur Ko-fi",
        "nav": {
            "home": "Accueil",
            "download": "Télécharger",
            "how-it-works": "Fonctionnement",
            "dual-monitor-wallpaper-windows-11": "Double écran",
            "faq": "FAQ",
            "compare": "Comparatif",
            "use-cases": "Cas d'usage",
            "dual-monitor-wallpaper-without-cropping": "Guide sans rognage",
            "mixed-monitor-wallpaper-setup": "Écrans mixtes",
        },
        "footer_about_title": "WallCraft Pro",
        "footer_about_text": "Application Windows open source pour créer, découper et appliquer des fonds d'écran sur des configurations multi-écrans irrégulières, sans rognage ni déformation. Projet relié à Archi-IT Labs.",
        "footer_resources_title": "Pages",
        "footer_source_title": "Projet",
        "footer_source_text": f"Le code source est public sur GitHub, et la release Windows packagée actuelle est maintenant disponible via GitHub Releases en version v{PRODUCT_VERSION}.",
        "footer_hub_label": "Voir Archi-IT Labs",
        "download_now": f"Télécharger v{PRODUCT_VERSION} pour Windows",
        "view_source": "Voir sur GitHub",
        "view_releases": "Ouvrir les releases GitHub",
        "learn_more": "Comprendre le fonctionnement",
        "related_title": "Continuer la visite",
        "ready_title": "Prêt à créer un fond d'écran qui respecte vraiment tes écrans ?",
        "ready_text": "Télécharge le build actuel, teste ta configuration multi-écrans et garde le dépôt GitHub sous la main pour les mises à jour et le code source.",
        "read_page": "Voir la page",
        "updated": "Mis à jour",
    },
    "es": {
        "name": "Español",
        "locale": "es_ES",
        "tagline": "Estudio open source de fondos para varios monitores",
        "skip": "Ir al contenido",
        "support": "Apoyarme en Ko-fi",
        "nav": {
            "home": "Inicio",
            "download": "Descargar",
            "how-it-works": "Cómo funciona",
            "dual-monitor-wallpaper-windows-11": "Doble monitor",
            "faq": "FAQ",
            "compare": "Comparar",
            "use-cases": "Casos de uso",
            "dual-monitor-wallpaper-without-cropping": "Guía sin recortes",
            "mixed-monitor-wallpaper-setup": "Monitores mixtos",
        },
        "footer_about_title": "WallCraft Pro",
        "footer_about_text": "Aplicación open source para Windows que crea, divide y aplica fondos en configuraciones con monitores desiguales, sin recortar ni deformar las imágenes. Proyecto conectado a Archi-IT Labs.",
        "footer_resources_title": "Paginas",
        "footer_source_title": "Proyecto",
        "footer_source_text": f"El código fuente es público en GitHub y la release empaquetada actual para Windows ya está disponible en GitHub Releases como v{PRODUCT_VERSION}.",
        "footer_hub_label": "Ver Archi-IT Labs",
        "download_now": f"Descargar v{PRODUCT_VERSION} para Windows",
        "view_source": "Ver en GitHub",
        "view_releases": "Abrir releases de GitHub",
        "learn_more": "Ver cómo funciona",
        "related_title": "Seguir explorando",
        "ready_title": "Listo para crear un fondo que de verdad encaje con tu escritorio?",
        "ready_text": "Descarga la build actual, prueba tu disposición de monitores y deja el repositorio de GitHub a mano para actualizaciones y código fuente.",
        "read_page": "Leer página",
        "updated": "Actualizado",
    },
    "de": {
        "name": "Deutsch",
        "locale": "de_DE",
        "tagline": "Open-Source-Studio für Multi-Monitor-Wallpaper",
        "skip": "Zum Inhalt springen",
        "support": "Mich auf Ko-fi unterstützen",
        "nav": {
            "home": "Start",
            "download": "Download",
            "how-it-works": "So funktioniert es",
            "dual-monitor-wallpaper-windows-11": "Dual Monitor",
            "faq": "FAQ",
            "compare": "Vergleich",
            "use-cases": "Einsatzszenarien",
            "dual-monitor-wallpaper-without-cropping": "Ohne Zuschnitt",
            "mixed-monitor-wallpaper-setup": "Gemischte Monitore",
        },
        "footer_about_title": "WallCraft Pro",
        "footer_about_text": "Open-Source-Windows-App zum Erstellen, Aufteilen und Anwenden von Wallpapern für ungleichmäßige Multi-Monitor-Setups, ohne Zuschnitt oder Verzerrung. Mit Archi-IT Labs verbunden.",
        "footer_resources_title": "Seiten",
        "footer_source_title": "Projekt",
        "footer_source_text": f"Der Quellcode ist auf GitHub öffentlich, und die aktuelle paketierte Windows-Release ist jetzt über GitHub Releases als v{PRODUCT_VERSION} verfügbar.",
        "footer_hub_label": "Archi-IT Labs ansehen",
        "download_now": f"v{PRODUCT_VERSION} für Windows herunterladen",
        "view_source": "Auf GitHub ansehen",
        "view_releases": "GitHub-Releases öffnen",
        "learn_more": "So funktioniert es",
        "related_title": "Weiterlesen",
        "ready_title": "Bereit für ein Wallpaper, das wirklich zu deinem Setup passt?",
        "ready_text": "Lade den aktuellen Build herunter, teste dein Multi-Monitor-Layout und nutze das GitHub-Repository für Updates und Quellcode.",
        "read_page": "Seite lesen",
        "updated": "Aktualisiert",
    },
}

FAQ_ITEMS = {
    "en": [
        ("Does WallCraft Pro crop images?", "Not by default. Fit mode keeps every image whole, so empty space can remain. The optional Fill mode covers the screens and crops each photo around detected faces, never distorting it."),
        ("Can one image line up across screens of different sizes?", "Yes. Turn on Real screen size in the Screens menu: each screen is placed by its physical size and the gap between panels, so a horizon stays straight across a 27-inch and a 24-inch display."),
        ("Does it work with different monitor sizes?", "Yes. Mixed resolutions, different heights, and uneven desk layouts are the core use case."),
        ("Can I export and split by screen?", "Yes. The app can export a large composition and split the result into per-monitor images mapped to your physical setup."),
        ("Can it apply wallpapers directly on Windows?", "Yes. The project uses the native Windows desktop wallpaper API when available, with a span fallback when needed."),
        ("Is it open source?", "Yes. The source code is public on GitHub, which helps with trust, inspection, and community contributions."),
        ("Is there a versioned GitHub release already?", f"Yes. The current packaged release is v{PRODUCT_VERSION} on GitHub Releases, with a Windows executable and its SHA-256 checksum."),
        ("Does it keep my wallpaper when I dock or undock my laptop?", "Yes. WallCraft remembers one wallpaper per screen setup and reapplies it when screens change or when Windows restores a theme. It can stay in the notification area, start with Windows and rotate images from a folder."),
    ],
    "fr": [
        ("WallCraft Pro rogne-t-il les images ?", "Pas par défaut. Le mode Ajuster garde chaque image entière, il peut donc rester des marges. Le mode Remplir, au choix, couvre les écrans et recadre chaque photo autour des visages détectés, sans jamais la déformer."),
        ("Une image peut-elle rester alignée entre des écrans de tailles différentes ?", "Oui. Activez la taille réelle dans le menu Écrans : chaque écran est placé selon sa taille physique et l'espace entre les dalles, si bien qu'une ligne d'horizon reste droite entre un 27 pouces et un 24 pouces."),
        ("Est-ce que cela fonctionne avec des écrans de tailles différentes ?", "Oui. Les résolutions mixtes, les hauteurs différentes et les dispositions irrégulières sont précisément le cas d'usage visé."),
        ("Peut-on exporter et découper par écran ?", "Oui. L'application peut exporter une grande composition puis la découper en images par moniteur selon ta disposition physique."),
        ("Peut-elle appliquer le fond d'écran directement sur Windows ?", "Oui. Le projet utilise l'API native de fond d'écran Windows quand elle est disponible, avec un mode panorama en secours."),
        ("Le projet est-il open source ?", "Oui. Le code source est public sur GitHub, ce qui aide pour la confiance, l'inspection et les contributions."),
        ("Y a-t-il déjà une vraie GitHub Release versionnée ?", f"Oui. La version packagée actuelle est la v{PRODUCT_VERSION} sur GitHub Releases, avec un exécutable Windows et son empreinte SHA-256."),
        ("Le fond reste-t-il en place quand je branche ou débranche mon portable ?", "Oui. WallCraft mémorise un fond par configuration d'écrans et le réapplique quand les écrans changent ou quand Windows remet un thème. Il peut rester dans la zone de notification, se lancer au démarrage et faire tourner les images d'un dossier."),
    ],
    "es": [
        ("¿WallCraft Pro recorta las imágenes?", "No por defecto. El modo Ajustar mantiene cada imagen entera, así que puede quedar espacio vacío. El modo Rellenar, opcional, cubre las pantallas y recorta cada foto alrededor de las caras detectadas, sin deformarla nunca."),
        ("¿Una imagen puede quedar alineada entre pantallas de distinto tamaño?", "Sí. Active el tamaño real en el menú Pantallas: cada pantalla se coloca según su tamaño físico y el espacio entre paneles, así un horizonte sigue recto entre un monitor de 27 y otro de 24 pulgadas."),
        ("¿Funciona con monitores de distintos tamaños?", "Sí. Resoluciones mixtas, alturas distintas y disposiciones irregulares son justo el caso de uso principal."),
        ("¿Puedo exportar y dividir por pantalla?", "Sí. La aplicación puede exportar una composición grande y dividir el resultado en imágenes por monitor."),
        ("¿Puede aplicar el fondo directamente en Windows?", "Sí. El proyecto usa la API nativa de fondos de Windows cuando está disponible, con modo panorámico como respaldo."),
        ("¿Es open source?", "Sí. El código fuente es público en GitHub, lo que mejora la confianza, la revisión y las contribuciones."),
        ("¿Ya existe una release versionada en GitHub?", f"Sí. La versión empaquetada actual es la v{PRODUCT_VERSION} en GitHub Releases, con un ejecutable para Windows y su huella SHA-256."),
        ("¿Se mantiene el fondo al conectar o desconectar el portátil?", "Sí. WallCraft guarda un fondo por configuración de pantallas y lo vuelve a aplicar cuando cambian las pantallas o cuando Windows restaura un tema. Puede quedarse en el área de notificación, iniciarse con Windows y rotar imágenes de una carpeta."),
    ],
    "de": [
        ("Schneidet WallCraft Pro Bilder zu?", "Standardmäßig nicht. Der Modus Einpassen zeigt jedes Bild vollständig, daher kann Leerraum bleiben. Der optionale Modus Füllen bedeckt die Bildschirme und schneidet jedes Foto um erkannte Gesichter zu, ohne es je zu verzerren."),
        ("Bleibt ein Bild über unterschiedlich große Bildschirme ausgerichtet?", "Ja. Aktivieren Sie die reale Größe im Menü Bildschirme: Jeder Bildschirm wird nach seiner physischen Größe und dem Abstand zwischen den Panels platziert, sodass ein Horizont zwischen einem 27- und einem 24-Zoll-Monitor gerade bleibt."),
        ("Funktioniert es mit unterschiedlich großen Monitoren?", "Ja. Gemischte Auflösungen, verschiedene Höhen und ungleichmäßige Setups sind genau der Kern-Anwendungsfall."),
        ("Kann ich nach Monitor exportieren und aufteilen?", "Ja. Die App kann eine große Komposition exportieren und das Ergebnis passend zu deinem physischen Setup in Einzelbilder pro Monitor teilen."),
        ("Kann die App Wallpaper direkt unter Windows anwenden?", "Ja. Das Projekt nutzt die native Windows-Desktop-Wallpaper-API, wenn sie verfügbar ist, und wechselt sonst auf einen Span-Fallback."),
        ("Ist das Projekt Open Source?", "Ja. Der Quellcode ist auf GitHub öffentlich, was Vertrauen, Prüfbarkeit und Beiträge erleichtert."),
        ("Gibt es schon eine versionierte GitHub-Release?", f"Ja. Die aktuelle paketierte Version ist v{PRODUCT_VERSION} in GitHub Releases, mit einer Windows-EXE und ihrer SHA-256-Prüfsumme."),
        ("Bleibt das Hintergrundbild erhalten, wenn ich den Laptop an- oder abdocke?", "Ja. WallCraft merkt sich ein Hintergrundbild pro Bildschirmkonfiguration und wendet es erneut an, wenn sich die Bildschirme ändern oder Windows ein Design wiederherstellt. Es kann im Infobereich bleiben, mit Windows starten und Bilder aus einem Ordner wechseln."),
    ],
}


def page_dir(lang, key):
    slug = SLUGS[key]
    if key == "home":
        return HTML_ROOT / lang
    return HTML_ROOT / lang / slug


def page_url(lang, key):
    slug = SLUGS[key]
    if key == "home":
        return f"{BASE_URL}{lang}/"
    return f"{BASE_URL}{lang}/{slug}/"


def rel_prefix(key):
    return "../" if key == "home" else "../../"


def asset_url(relative):
    return f"{BASE_URL}{relative}"

PAGES = {
    "en": {
        "home": {
            "meta_title": "WallCraft Pro - Multi-Monitor Wallpaper Generator for Windows 10/11",
            "meta_description": "Create and apply wallpapers across dual, triple, and mixed-size monitors on Windows 10/11. No crop, no distortion, preview, export, and per-screen split.",
            "hero_badge": "Built for Windows 10 and 11",
            "hero_title": "Create perfect wallpapers for mixed monitor setups",
            "hero_lead": "WallCraft Pro helps you compose, split, and apply wallpapers across dual, triple, vertical, ultrawide, and mixed-size monitors without cropping or distortion.",
            "hero_points": [
                "100% image visibility with a fit-inside engine.",
                "Six layout modes, including maximum optimization.",
                "Export, split by monitor, or apply directly on Windows."
            ],
            "hero_caption_title": "Real screenshot of the current interface",
            "hero_caption_text": "The main workspace combines preview, layout selection, image controls, and output actions in one Windows app.",
            "sections": [
                {"type": "cards", "title": "Guides and specific setups", "text": "Specific resources for the most common multi-monitor configurations.", "cards": [
                    {"title": "Dual monitor wallpaper on Windows 11", "text": "Solve the common dual-monitor wallpaper problem without forced cropping.", "page": "dual-monitor-wallpaper-windows-11"},
                    {"title": "No crop workflow", "text": "Keep every photo visible, even across uneven screens.", "page": "dual-monitor-wallpaper-without-cropping"},
                    {"title": "Mixed monitor sizes", "text": "Handle different resolutions, heights, and aspect ratios cleanly.", "page": "mixed-monitor-wallpaper-setup"}
                ]},
                {"type": "steps", "title": "How the workflow works", "text": "WallCraft is a composition pipeline, not just a wallpaper picker.", "steps": [
                    {"title": "Import photos", "text": "Build the project from real images instead of one fixed panorama."},
                    {"title": "Choose a layout", "text": "Use one of six algorithms depending on your setup."},
                    {"title": "Preview and tweak", "text": "Inspect the geometry, reorder, and adjust images."},
                    {"title": "Export, split, or apply", "text": "Finish with the output that matches your desk."}
                ]},
                {"type": "shot", "title": "Proof instead of vague promises", "text": "A second screenshot shows the optimization-oriented view and makes the product feel real.", "image": SCREEN_2, "caption_title": "Maximum optimization preview", "caption_text": "The heuristic layout tries many geometric permutations to reduce wasted space across mixed screens."},
                {"type": "faq", "title": "Questions before download", "text": "These answers remove the trust objections that usually stop a first click.", "items": FAQ_ITEMS["en"][:4]},
                {"type": "links", "title": "Learn more about WallCraft Pro", "text": "Explore all features and details of the application.", "links": ["download", "how-it-works", "use-cases", "compare", "faq"]}
            ]
        },
        "download": {
            "meta_title": "Download WallCraft Pro v1.0.0 for Windows 10/11",
            "meta_description": "Download WallCraft Pro v1.0.0 for Windows 10/11, open the GitHub repository, and read release notes from the official GitHub Releases page.",
            "hero_badge": "GitHub Release v1.0.0",
            "hero_title": "Download WallCraft Pro v1.0.0 for Windows 10/11",
            "hero_lead": "Get the first packaged Windows release of WallCraft Pro, inspect the source code, and verify the release notes from GitHub.",
            "sections": [
                {"type": "cards", "title": "Choose your path", "text": "v1.0.0 is live on GitHub Releases, with one clean path for download, source, and release notes.", "cards": [
                    {"title": "Official Windows release", "text": "Download the packaged executable for Windows 10/11.", "url": DOWNLOAD_URL, "cta": f"Download v{PRODUCT_VERSION} for Windows"},
                    {"title": "Source code", "text": "Inspect the repository, star the project, or build from source.", "url": REPO_URL, "cta": "View on GitHub"},
                    {"title": "Release notes", "text": "Open the GitHub Releases page for version history and future updates.", "url": RELEASES_URL, "cta": "Open GitHub releases"}
                ]},
                {"type": "text", "title": "Current release details", "text": "WallCraft has a stable downloadable release for Windows users.", "body": [
                    "The current public package is v1.0.0 for Windows.",
                    "The same GitHub Releases page will carry changelogs and future versions."
                ], "list": ["Windows 10/11 executable available now.", "Open source repository stays public.", "Version history now starts from v1.0.0."], "aside_title": "Current release", "aside_body": ["Filename: WallCraft-Pro-v1.0.0-Windows.exe.", "Release notes and future builds live on GitHub Releases."]},
                {"type": "shot", "title": "Verified workspace", "text": "Preview the application interface before you download.", "image": SCREEN_1, "caption_title": "Main workspace", "caption_text": "Preview, layout selection, editing controls, and output actions are already visible in the current UI."},
                {"type": "links", "title": "Other useful resources", "text": "More information to help you get started.", "links": ["how-it-works", "faq", "compare"]}
            ]
        },
        "how-it-works": {
            "meta_title": "How WallCraft Pro Works on Mixed Monitor Setups",
            "meta_description": "See how WallCraft Pro detects screens, preserves image visibility, chooses layouts, and exports or applies wallpapers across mixed monitors.",
            "hero_badge": "Product walkthrough",
            "hero_title": "How WallCraft builds wallpapers for mixed monitor setups",
            "hero_lead": "This page translates the product promise into a clear, practical workflow.",
            "sections": [
                {"type": "steps", "title": "Five steps from photo folder to desktop", "text": "The internal logic handles complex geometry to ensure a perfect fit.", "steps": [
                    {"title": "Detect the real screen map", "text": "WallCraft reads the physical layout of the monitors."},
                    {"title": "Keep every image inside its frame", "text": "Fit-inside protects the original ratio and avoids cropping."},
                    {"title": "Run a layout algorithm", "text": "Choose between six layout strategies."},
                    {"title": "Preview and tweak", "text": "Adjust the composition before output."},
                    {"title": "Export, split, or apply", "text": "Use the output that fits the desk."}
                ]},
                {"type": "shot", "title": "Unified interface", "text": "An efficient dashboard for all your wallpaper tasks.", "image": SCREEN_1, "caption_title": "One place for preview and output", "caption_text": "The tool combines all necessary controls in a single, intuitive view."},
                {"type": "links", "title": "Continue your tour", "text": "Discover more about what WallCraft Pro can do.", "links": ["download", "use-cases", "faq"]}
            ]
        },
        "dual-monitor-wallpaper-windows-11": {
            "meta_title": "Dual Monitor Wallpaper on Windows 11 Without Cropping",
            "meta_description": "Create a dual monitor wallpaper on Windows 11 without cropping or distortion, even when the monitors have different sizes or alignments.",
            "hero_badge": "Optimization guide",
            "hero_title": "Create a dual monitor wallpaper on Windows 11 without cropping",
            "hero_lead": "Standard wallpapers often fail on dual-monitor setups with different sizes. WallCraft Pro fixes this.",
            "sections": [
                {"type": "text", "title": "Why dual-monitor wallpapers go wrong", "text": "Two screens usually do not share one ideal rectangle.", "body": ["One display may be taller, offset, or vertical.", "Standard 'Fill' or 'Span' modes often lead to frustrating results on uneven screens."], "list": ["Different heights.", "Different aspect ratios.", "Focal point landing on a bezel."], "aside_title": "How WallCraft solves this", "aside_body": ["WallCraft keeps your images visible instead of forcing a panoramic crop.", "It treats each screen as a unique frame within the composition."]},
                {"type": "cards", "title": "Key Advantages", "text": "Practical features for everyday multi-monitor users.", "cards": [
                    {"title": "Fit-inside placement", "text": "Keep the full image visible instead of trimming it."},
                    {"title": "Layout choice", "text": "Choose a strategy that fits the desk."},
                    {"title": "Per-screen output", "text": "Export and split the final result cleanly."}
                ]},
                {"type": "links", "title": "More guides", "text": "Specific help for different configurations.", "links": ["download", "dual-monitor-wallpaper-without-cropping", "faq"]}
            ]
        },
        "faq": {
            "meta_title": "WallCraft Pro FAQ",
            "meta_description": "Read the WallCraft Pro FAQ about cropping, mixed monitor sizes, Windows support, split export, open source access, and download state.",
            "hero_badge": "Support & Documentation",
            "hero_title": "Frequently asked questions about WallCraft Pro",
            "hero_lead": "Find answers to the most common questions about the application.",
            "sections": [
                {"type": "faq", "title": "WallCraft Pro FAQ", "text": "Common questions and detailed answers.", "items": FAQ_ITEMS["en"]},
                {"type": "links", "title": "What's next?", "text": "Download the app or compare it with other tools.", "links": ["download", "compare", "how-it-works"]}
            ]
        },
        "compare": {
            "meta_title": "Compare WallCraft Pro with Other Wallpaper Options",
            "meta_description": "Compare WallCraft Pro with Windows personalization, Wallpaper Engine, and DisplayFusion to choose the right tool for static mixed-monitor wallpapers.",
            "hero_badge": "Comparison guide",
            "hero_title": "Compare WallCraft Pro with common wallpaper alternatives",
            "hero_lead": "Choose the right tool for your specific multi-monitor needs.",
            "sections": [
                {"type": "compare", "title": "Positioning by use case", "text": "Every tool has its strengths. See where WallCraft Pro excels.", "headers": ["Option", "Best for", "Main focus", "Where WallCraft is stronger"], "rows": [
                    ["WallCraft Pro", "Static wallpapers on mixed monitor layouts", "No-crop composition, split export, native Windows apply", "Purpose-built for preserving the full image on uneven screens"],
                    ["Windows personalization", "Simple built-in background changes", "Basic wallpaper and theme handling", "Better when you need more than fill or span"],
                    ["Wallpaper Engine", "Animated or live wallpapers", "Motion backgrounds and workshop-style content", "Better when the priority is static photo composition"],
                    ["DisplayFusion", "Broader multi-monitor desktop management", "Window management plus monitor utilities", "Better when the main goal is wallpaper composition itself"]
                ], "notes": [
                    {"title": "Choose the right category", "text": "WallCraft focuses on static image composition for uneven screens."},
                    {"title": "Focused utility", "text": "The core promise is simple: keep the image visible and make the setup look intentional."}
                ]},
                {"type": "links", "title": "What tools do you need?", "text": "Ready to decide? Explore the relevant sections.", "links": ["download", "dual-monitor-wallpaper-windows-11", "mixed-monitor-wallpaper-setup"]}
            ]
        },
        "use-cases": {
            "meta_title": "WallCraft Pro Use Cases for Dual, Triple, and Mixed Monitors",
            "meta_description": "Explore WallCraft Pro use cases for dual monitors, triple screens, laptop plus external displays, ultrawide setups, and mixed monitor sizes.",
            "hero_badge": "User scenarios",
            "hero_title": "Real setups, real solutions",
            "hero_lead": "See how WallCraft Pro handles real-world desk configurations.",
            "sections": [
                {"type": "cards", "title": "Common desk setups", "text": "Examples of how users apply WallCraft Pro to their daily workspace.", "cards": [
                    {"title": "Laptop plus external monitor", "text": "Useful when one screen is smaller or offset."},
                    {"title": "Vertical plus ultrawide", "text": "A creator desk layout where ordinary panoramas break immediately."},
                    {"title": "Triple monitor workstation", "text": "Helpful when you want a coherent photo wall across three screens."},
                    {"title": "Different monitor heights", "text": "Important when screen edges do not line up physically."},
                    {"title": "Photo-heavy setups", "text": "A strong fit when preserving the full image matters more than edge-to-edge fill."},
                    {"title": "Artwork and illustration", "text": "Good for collections where distortion would be worse than small bars."}
                ]},
                {"type": "links", "title": "Discover more", "text": "Learn how to achieve these setups yourself.", "links": ["download", "how-it-works", "dual-monitor-wallpaper-without-cropping"]}
            ]
        },
        "dual-monitor-wallpaper-without-cropping": {
            "meta_title": "How to Make a Dual Monitor Wallpaper Without Cropping",
            "meta_description": "Learn how to make a dual monitor wallpaper without cropping by using fit-inside placement, layout strategies, and per-screen export.",
            "hero_badge": "Step-by-step guide",
            "hero_title": "How to make a dual monitor wallpaper without cropping",
            "hero_lead": "A practical guide to keeping your artwork intact across multiple monitors.",
            "sections": [
                {"type": "steps", "title": "A reliable no-crop workflow", "text": "Manage empty space effectively while keeping the original image proportions.", "steps": [
                    {"title": "Start with source images worth preserving", "text": "Choose images where keeping the full frame matters."},
                    {"title": "Use fit-inside instead of forced fill", "text": "That keeps the image visible and respects the original ratio."},
                    {"title": "Choose a layout that fits the desk", "text": "Maximum optimization can reduce visible bars."},
                    {"title": "Split the output per monitor", "text": "Avoid manual slicing in a second image editor."}
                ]},
                {"type": "text", "title": "Why this matters", "text": "Standard tools often force a destructive crop on your favorite photos.", "body": ["Avoiding cropping captures the original intent of the photographer or artist.", "This makes WallCraft Pro ideal for high-quality backgrounds and photography portfolio setups."], "list": ["No destructive crop.", "Better fit for photos and art.", "Clear bridge into download and FAQ pages."]},
                {"type": "links", "title": "Related resources", "text": "Continue exploring multi-monitor wallpaper techniques.", "links": ["download", "mixed-monitor-wallpaper-setup", "faq"]}
            ]
        },
        "mixed-monitor-wallpaper-setup": {
            "meta_title": "Best Wallpaper Setup for Mixed Monitor Sizes",
            "meta_description": "Find the best wallpaper setup for mixed monitor sizes, different heights, and uneven desktop layouts on Windows 10/11.",
            "hero_badge": "Advanced setup guide",
            "hero_title": "The best wallpaper setup for mixed monitor sizes",
            "hero_lead": "Handling uneven geometry is where WallCraft Pro shines.",
            "sections": [
                {"type": "text", "title": "The geometry challenge", "text": "When one screen is taller, wider, or rotated, the challenge is no longer just the photo.", "body": ["A good setup acknowledges that the monitors do not form one perfect rectangle.", "The best workflow adapts to uneven geometry instead of flattening everything into one crop."], "list": ["Different resolutions.", "Different physical heights.", "Different aspect ratios."], "aside_title": "WallCraft's approach", "aside_body": ["It treats the monitor map as part of the composition workflow.", "This ensures your wallpaper feels intentional on your real desk."]},
                {"type": "cards", "title": "Optimized layouts", "text": "Choose the algorithm that best matches your monitor arrangement.", "cards": [
                    {"title": "Maximum optimization", "text": "Best when reducing visible bars is the highest priority."},
                    {"title": "Justified lines", "text": "Good when you want a more editorial rhythm."},
                    {"title": "Grid or strips", "text": "Useful when visual order matters more than aggressive packing."}
                ]},
                {"type": "links", "title": "Take the next step", "text": "Ready to build your setup?", "links": ["download", "dual-monitor-wallpaper-without-cropping", "use-cases"]}
            ]
        },
    },
    "es": {
        "home": {
            "meta_title": "WallCraft Pro - Generador de fondos para varios monitores en Windows 10/11",
            "meta_description": "Crea y aplica fondos para configuraciones de doble monitor, triple monitor y monitores de distinto tamaño en Windows 10/11, sin recortes ni deformación.",
            "hero_badge": "Creado para Windows 10 y 11",
            "hero_title": "Crear un fondo limpio para monitores de distinto tamaño",
            "hero_lead": "WallCraft Pro ayuda a componer, dividir y aplicar fondos en configuraciones doble monitor, triple monitor, verticales, ultrawide y mixtas, sin recortes ni deformación.",
            "hero_points": [
                "Visibilidad total de la imagen con fit-inside.",
                "Seis modos de layout optimizados.",
                "Exportar, dividir por pantalla o aplicar en Windows."
            ],
            "hero_caption_title": "Captura real de la interfaz",
            "hero_caption_text": "El espacio principal combina vista previa, layouts y controles en una sola app de Windows.",
            "sections": [
                {"type": "cards", "title": "Guías y configuraciones", "text": "Recursos específicos para los casos más comunes de multi-monitores.", "cards": [
                    {"title": "Fondo doble monitor en Windows 11", "text": "Resolver el caso clásico de doble monitor sin recorte forzado.", "page": "dual-monitor-wallpaper-windows-11"},
                    {"title": "Flujo sin recortes", "text": "Mantener cada foto visible incluso en pantallas desiguales.", "page": "dual-monitor-wallpaper-without-cropping"},
                    {"title": "Monitores de distinto tamaño", "text": "Gestionar resoluciones, alturas y proporciones distintas.", "page": "mixed-monitor-wallpaper-setup"}
                ]},
                {"type": "steps", "title": "Cómo funciona el flujo", "text": "WallCraft es un flujo de composición completo para tus fondos.", "steps": [
                    {"title": "Importar fotos", "text": "Trabajar con imágenes reales y no con un panorama fijo."},
                    {"title": "Elegir layout", "text": "Usar uno de los seis algoritmos según el escritorio."},
                    {"title": "Previsualizar y ajustar", "text": "Comprobar la geometría y retocar si hace falta."},
                    {"title": "Exportar, dividir o aplicar", "text": "Terminar con la salida adecuada para el setup."}
                ]},
                {"type": "shot", "title": "Prueba real", "text": "Descubre la interfaz optimizada para la gestión multi-monitores.", "image": SCREEN_2, "caption_title": "Vista de optimización máxima", "caption_text": "El layout heurístico calcula las mejores permutaciones para reducir el vacío en pantallas mixtas."},
                {"type": "faq", "title": "Preguntas frecuentes", "text": "Respuestas a las dudas más comunes antes de descargar.", "items": FAQ_ITEMS["es"][:4]},
                {"type": "links", "title": "Saber más", "text": "Explora todas las funcionalidades de WallCraft Pro.", "links": ["download", "how-it-works", "use-cases", "compare", "faq"]}
            ]
        },
        "download": {
            "meta_title": "Descargar WallCraft Pro v1.0.0 para Windows 10/11",
            "meta_description": "Descarga WallCraft Pro v1.0.0 para Windows 10/11, consulta el repositorio de GitHub y lee las notas de versión.",
            "hero_badge": "GitHub Release v1.0.0",
            "hero_title": "Descargar WallCraft Pro v1.0.0 para Windows 10/11",
            "hero_lead": "Consigue la primera versión oficial para Windows, revisa el código fuente y las notas de versión en GitHub.",
            "sections": [
                {"type": "cards", "title": "Acceso al producto", "text": "La v1.0.0 es la versión oficial disponible en GitHub Releases.", "cards": [
                    {"title": "Release oficial para Windows", "text": "Descargar el ejecutable para Windows 10/11.", "url": DOWNLOAD_URL, "cta": f"Descargar v{PRODUCT_VERSION} para Windows"},
                    {"title": "Código fuente", "text": "Revisar el repositorio o compilar desde la fuente.", "url": REPO_URL, "cta": "Ver en GitHub"},
                    {"title": "Notas de versión", "text": "Abrir GitHub Releases para ver el historial.", "url": RELEASES_URL, "cta": "Ver releases"}
                ]},
                {"type": "text", "title": "Detalles de la versión", "text": "WallCraft ya está disponible como versión estable para Windows.", "body": ["El paquete actual es la v1.0.0 para Windows.", "La página de lanzamientos de GitHub contiene el historial de cambios."], "list": ["Ejecutable Windows 10/11 disponible.", "Repositorio open source público.", "Historial iniciado con la v1.0.0."], "aside_title": "Versión actual", "aside_body": ["Archivo: WallCraft-Pro-v1.0.0-Windows.exe.", "Notas y futuros builds disponibles en GitHub."]},
                {"type": "shot", "title": "Vista previa", "text": "Revisa la interfaz antes de realizar la descarga.", "image": SCREEN_1, "caption_title": "Espacio de trabajo", "caption_text": "Todo lo necesario en una sola vista: previa, layouts y salidas."},
                {"type": "links", "title": "Otros recursos", "text": "Más páginas para ayudarte a empezar.", "links": ["how-it-works", "faq", "compare"]}
            ]
        },
        "how-it-works": {
            "meta_title": "Cómo funciona WallCraft Pro en monitores mixtos",
            "meta_description": "Descubre cómo WallCraft Pro detecta pantallas, preserva la imagen, elige layouts y exporta fondos multi-monitores.",
            "hero_badge": "Tour del producto",
            "hero_title": "Cómo WallCraft crea fondos para escritorios mixtos",
            "hero_lead": "Un flujo de trabajo preciso que garantiza un ajuste perfecto en tus pantallas.",
            "sections": [
                {"type": "steps", "title": "Cinco pasos del archivo al escritorio", "text": "La lógica de WallCraft resuelve los desafíos geométricos complejos.", "steps": [
                    {"title": "Detectar el mapa real", "text": "Lee la disposición física de los monitores."},
                    {"title": "Mantener la imagen entera", "text": "Protege la proporción original sin recortar."},
                    {"title": "Algoritmo de layout", "text": "Elige entre seis estrategias inteligentes."},
                    {"title": "Previsualizar y ajustar", "text": "Ajusta la composición antes de aplicar."},
                    {"title": "Salida optimizada", "text": "Exporta o aplica directamente al escritorio."}
                ]},
                {"type": "shot", "title": "Interfaz unificada", "text": "Un panel eficiente para todas tus tareas de fondos.", "image": SCREEN_1, "caption_title": "Previa y salida juntas", "caption_text": "Evita saltar entre herramientas con una vista integrada."},
                {"type": "links", "title": "Seguir explorando", "text": "Descubre más sobre lo que WallCraft Pro puede hacer.", "links": ["download", "use-cases", "faq"]}
            ]
        },
        "dual-monitor-wallpaper-windows-11": {
            "meta_title": "Fondo para doble monitor en Windows 11 sin recortes",
            "meta_description": "Crea un fondo de pantalla para dos monitores en Windows 11 sin recortes ni distorsiones, incluso con pantallas de distintos tamaños.",
            "hero_title": "Crear un fondo para doble monitor en Windows 11 sin recortes",
            "hero_lead": "Los fondos estándar fallan en monitores mixtos. WallCraft Pro es la solución definitiva.",
            "sections": [
                {"type": "text", "title": "El problema de los monitores desiguales", "text": "Dos pantallas casi nunca forman un rectángulo perfecto.", "body": ["Una pantalla puede ser más alta o estar en vertical.", "Los modos estándar de Windows suelen deformar o cortar la imagen en estos casos."], "list": ["Alturas distintas.", "Ratios distintos.", "Sujeto cortado."], "aside_title": "Solución WallCraft", "aside_body": ["Mantiene la imagen visible en lugar de forzar un recorte.", "Se adapta a la geometría real de tu escritorio."]},
                {"type": "cards", "title": "Ventajas", "text": "Características prácticas para usuarios de varios monitores.", "cards": [
                    {"title": "Colocación fit-inside", "text": "Garantiza que toda la imagen sea visible."},
                    {"title": "Elección de layout", "text": "Elige la estrategia que mejor encaje."},
                    {"title": "Salida limpia", "text": "Exporta resultados específicos por pantalla."}
                ]},
                {"type": "links", "title": "Más guías", "text": "Ayuda específica para otras configuraciones.", "links": ["download", "dual-monitor-wallpaper-without-cropping", "faq"]}
            ]
        },
        "faq": {
            "meta_title": "FAQ de WallCraft Pro",
            "meta_description": "Preguntas frecuentes sobre WallCraft Pro, el generador de fondos de pantalla para varios monitores.",
            "hero_title": "Preguntas frecuentes sobre WallCraft Pro",
            "hero_lead": "Respuestas a las dudas más comunes sobre la aplicación.",
            "sections": [
                {"type": "faq", "title": "FAQ WallCraft Pro", "text": "Preguntas y respuestas detalladas.", "items": FAQ_ITEMS["es"]},
                {"type": "links", "title": "Siguiente paso", "text": "Descarga la app o compárala con otras opciones.", "links": ["download", "compare", "how-it-works"]}
            ]
        },
        "compare": {
            "meta_title": "Comparar WallCraft Pro con otras opciones",
            "meta_description": "Comparativa de WallCraft Pro con Windows, Wallpaper Engine y DisplayFusion para configuraciones multi-monitor.",
            "hero_title": "Comparar WallCraft Pro con alternativas comunes",
            "hero_lead": "Elige la herramienta adecuada para tus necesidades multi-monitor.",
            "sections": [
                {"type": "compare", "title": "Uso por caso", "text": "Cada herramienta tiene sus puntos fuertes.", "headers": ["Opción", "Mejor para", "Foco", "Punto fuerte de WallCraft"], "rows": [
                    ["WallCraft Pro", "Fondos estáticos en pantallas mixtas", "Sin recortes, división, aplicación nativa", "Hecho para preservar la imagen entera"],
                    ["Personalización Windows", "Cambios básicos", "Gestión nativa simple", "Limitado para setups complejos"],
                    ["Wallpaper Engine", "Fondos animados", "Interacción y comunidad", "Menos optimizado para fotos estáticas"],
                    ["DisplayFusion", "Gestión global de escritorio", "Ventanas y productividad", "Más complejo para solo fondos"]
                ], "notes": [
                    {"title": "Elige tu categoría", "text": "WallCraft se centra en imágenes estáticas para pantallas desiguales."},
                    {"title": "Utilidad enfocada", "text": "La promesa es clara: mantener la imagen visible y el setup limpio."}
                ]},
                {"type": "links", "title": "Decídete", "text": "¿Listo para elegir? Revisa las secciones relevantes.", "links": ["download", "dual-monitor-wallpaper-windows-11", "mixed-monitor-wallpaper-setup"]}
            ]
        },
        "use-cases": {
            "meta_title": "Casos de uso de WallCraft Pro",
            "meta_description": "Ejemplos reales de uso de WallCraft Pro con portátiles, pantallas verticales y estaciones de trabajo con varios monitores.",
            "hero_title": "Escritorios reales, soluciones reales",
            "hero_lead": "Mira cómo WallCraft Pro se adapta a distintas configuraciones.",
            "sections": [
                {"type": "cards", "title": "Setups comunes", "text": "Ejemplos de uso diario con WallCraft Pro.", "cards": [
                    {"title": "Portátil más monitor", "text": "Ideal cuando una pantalla es más pequeña."},
                    {"title": "Vertical más panorámico", "text": "Donde fallan todos los fondos automáticos."},
                    {"title": "Estación triple monitor", "text": "Crea una pared de imágenes coherente."},
                    {"title": "Alturas diferentes", "text": "Cuando los bordes no se alinean físicamente."},
                    {"title": "Foco en fotografía", "text": "Preserva la imagen sin recortes destructivos."},
                    {"title": "Arte e ilustración", "text": "Evita deformaciones molestas."}
                ]},
                {"type": "links", "title": "Descubrir más", "text": "Aprende a montar estas configuraciones.", "links": ["download", "how-it-works", "dual-monitor-wallpaper-without-cropping"]}
            ]
        },
        "dual-monitor-wallpaper-without-cropping": {
            "meta_title": "Cómo hacer un fondo para doble monitor sin recortes",
            "meta_description": "Guía práctica para crear fondos de pantalla sin recortes en configuraciones de doble monitor.",
            "hero_title": "Cómo hacer un fondo para doble monitor sin recortes",
            "hero_lead": "Guía práctica para mantener tus imágenes intactas.",
            "sections": [
                {"type": "steps", "title": "Workflow sin recortes", "text": "Gestiona el espacio vacío respetando las proporciones originales.", "steps": [
                    {"title": "Imágenes que valen la pena", "text": "Usa fotos donde el encuadre original importa."},
                    {"title": "Usar fit-inside", "text": "Mantiene la visibilidad y el ratio."},
                    {"title": "Elegir el layout", "text": "La optimización máxima reduce los espacios vacíos."},
                    {"title": "Dividir la salida", "text": "Evita cortes manuales en otros editores."}
                ]},
                {"type": "text", "title": "Por qué es importante", "text": "Las herramientas estándar suelen destruir el encuadre original.", "body": ["Respetar el encuadre es respetar la intención del artista.", "WallCraft Pro es ideal para amantes de la fotografía de alta calidad."], "list": ["Sin recortes destructivos.", "Mejor ajuste para arte.", "Camino directo a la descarga."], "aside_title": "Dato", "aside_body": ["Más del 80% de los usuarios de multi-monitores sufren por recortes accidentales."]},
                {"type": "links", "title": "Relacionados", "text": "Sigue explorando técnicas de fondos.", "links": ["download", "mixed-monitor-wallpaper-setup", "faq"]}
            ]
        },
        "mixed-monitor-wallpaper-setup": {
            "meta_title": "Mejor configuración para pantallas de distinto tamaño",
            "meta_description": "Aprende a gestionar la geometría desigual de tus monitores para obtener el mejor fondo de pantalla posible.",
            "hero_title": "La mejor configuración para monitores de distinto tamaño",
            "hero_lead": "Gestionar la geometría desigual es donde brilla WallCraft Pro.",
            "sections": [
                {"type": "text", "title": "El reto geométrico", "text": "Un monitor más alto o vertical lo cambia todo.", "body": ["Un buen setup acepta que los monitores no son perfectos.", "El flujo se adapta a la geometría en lugar de forzar un crop global."], "list": ["Resoluciones mixtas.", "Alturas físicas distintas.", "Ratios variados."], "aside_title": "Aporte de WallCraft", "aside_body": ["Trata el mapa de pantallas como el centro del workflow.", "Tus fondos parecerán hechos a medida para tu escritorio."]},
                {"type": "cards", "title": "Layouts optimizados", "text": "Elige el algoritmo que mejor encaje con tu disposición.", "cards": [
                    {"title": "Optimización máxima", "text": "Reduce al máximo las barras visibles."},
                    {"title": "Líneas justificadas", "text": "Ideal para un equilibrio visual rítmico."},
                    {"title": "Cuadrículas", "text": "Práctico cuando prefieres un orden visual claro."}
                ]},
                {"type": "links", "title": "Danos una oportunidad", "text": "¿Listo para probarlo?", "links": ["download", "dual-monitor-wallpaper-without-cropping", "use-cases"]}
            ]
        },
    },
    "de": {
        "home": {
            "meta_title": "WallCraft Pro - Multi-Monitor-Wallpaper-Generator für Windows 10/11",
            "meta_description": "Erstelle und wende Wallpaper für Dual-, Triple- und gemischte Monitor-Setups unter Windows 10/11 an, ohne Zuschnitt oder Verzerrung.",
            "hero_badge": "Für Windows 10 und 11",
            "hero_title": "Saubere Wallpaper für unterschiedlich große Monitore",
            "hero_lead": "WallCraft Pro hilft beim Komponieren, Aufteilen und Anwenden von Wallpapern auf Dual-, Triple-, vertikalen und gemischten Setups ohne Zuschnitt.",
            "hero_points": [
                "Volle Bildsichtbarkeit durch Fit-Inside-Modus.",
                "Sechs Layout-Modi für jede Schreibtischform.",
                "Export, Aufteilung pro Monitor oder direkte Anwendung."
            ],
            "hero_caption_title": "Echter Screenshot",
            "hero_caption_text": "Der Hauptbereich vereint Vorschau, Layouts und Ausgabesteuerung in einer Windows-App.",
            "sections": [
                {"type": "cards", "title": "Anleitungen & Setups", "text": "Spezielle Ressourcen für die gängigsten Multi-Monitor-Szenarien.", "cards": [
                    {"title": "Dual-Monitor unter Windows 11", "text": "Den klassischen Fall ohne erzwungenen Zuschnitt lösen.", "page": "dual-monitor-wallpaper-windows-11"},
                    {"title": "Workflow ohne Zuschnitt", "text": "Bilder auf ungleichmäßigen Bildschirmen sichtbar halten.", "page": "dual-monitor-wallpaper-without-cropping"},
                    {"title": "Gemischte Monitorgrößen", "text": "Auflösungen und Höhen sauber handhaben.", "page": "mixed-monitor-wallpaper-setup"}
                ]},
                {"type": "steps", "title": "So funktioniert es", "text": "WallCraft ist ein vollständiger Workflow für Ihre Wallpaper-Komposition.", "steps": [
                    {"title": "Fotos importieren", "text": "Mit echten Bildern statt starren Panoramen arbeiten."},
                    {"title": "Layout wählen", "text": "Einen der sechs Algorithmen passend zum Setup nutzen."},
                    {"title": "Vorschau & Feinschliff", "text": "Geometrie prüfen und bei Bedarf anpassen."},
                    {"title": "Exportieren oder Anwenden", "text": "Mit der passenden Ausgabe für den Desk abschließen."}
                ]},
                {"type": "shot", "title": "Praxis-Check", "text": "Die optimierte Oberfläche für Multi-Monitor-Management.", "image": SCREEN_2, "caption_title": "Maximale Optimierung", "caption_text": "Der heuristische Layout-Algorithmus reduziert Leerraum auf gemischten Bildschirmen."},
                {"type": "faq", "title": "Häufige Fragen", "text": " Antworten auf die wichtigsten Fragen vor dem Download.", "items": FAQ_ITEMS["de"][:4]},
                {"type": "links", "title": "Mehr erfahren", "text": "Entdecken Sie alle Funktionen von WallCraft Pro.", "links": ["download", "how-it-works", "use-cases", "compare", "faq"]}
            ]
        },
        "download": {
            "meta_title": "WallCraft Pro v1.0.0 herunterladen",
            "meta_description": "Laden Sie die neueste Version von WallCraft Pro für Windows 10/11 von GitHub herunter.",
            "hero_badge": "GitHub Release v1.0.0",
            "hero_title": "WallCraft Pro v1.0.0 für Windows herunterladen",
            "hero_lead": "Holen Sie sich das erste offizielle Windows-Paket und prüfen Sie den Quellcode auf GitHub.",
            "sections": [
                {"type": "cards", "title": "Produkt-Zugang", "text": "v1.0.0 ist die offizielle Version auf GitHub Releases.", "cards": [
                    {"title": "Offizielle Windows-Release", "text": "Download der EXE für Windows 10/11.", "url": DOWNLOAD_URL, "cta": f"v{PRODUCT_VERSION} herunterladen"},
                    {"title": "Quellcode", "text": "Repository prüfen oder selbst kompilieren.", "url": REPO_URL, "cta": "Auf GitHub ansehen"},
                    {"title": "Release-Notes", "text": "Versionshistorie auf GitHub einsehen.", "url": RELEASES_URL, "cta": "Releases öffnen"}
                ]},
                {"type": "text", "title": "Release-Details", "text": "WallCraft ist nun als stabile Version für Windows verfügbar.", "body": ["Das aktuelle Paket ist v1.0.0 für Windows.", "Die GitHub-Releases-Seite enthält alle Changelogs."], "list": ["Windows 10/11 EXE verfügbar.", "Open-Source-Repository bleibt öffentlich.", "Historie ab v1.0.0 gestartet."], "aside_title": "Aktuell", "aside_body": ["Datei: WallCraft-Pro-v1.0.0-Windows.exe.", "Updates und Notes finden Sie auf GitHub."]},
                {"type": "shot", "title": "Visuelle Vorschau", "text": "Prüfen Sie die App vor dem Download.", "image": SCREEN_1, "caption_title": "Arbeitsbereich", "caption_text": "Alle Funktionen wie Vorschau und Layout in einer Ansicht."},
                {"type": "links", "title": "Ressourcen", "text": "Seiten, die Ihnen beim Einstieg helfen.", "links": ["how-it-works", "faq", "compare"]}
            ]
        },
        "how-it-works": {
            "meta_title": "So funktioniert WallCraft Pro",
            "meta_description": "Erfahren Sie, wie WallCraft Pro Hintergrundbilder für gemischte Monitor-Setups erstellt.",
            "hero_title": "Wallpaper-Erstellung für gemischte Desks",
            "hero_lead": "Ein präziser Workflow für perfekte Ergebnisse auf all Ihren Monitoren.",
            "sections": [
                {"type": "steps", "title": "In fünf Schritten zum Desktop", "text": "Die Logik von WallCraft löst komplexe geometrische Herausforderungen.", "steps": [
                    {"title": "Monitor-Karte lesen", "text": "Erkennt die physische Anordnung der Bildschirme."},
                    {"title": "Bilder ganz lassen", "text": "Fit-Inside schützt das Originalverhältnis."},
                    {"title": "Layout-Algorithmus", "text": "Wählen Sie aus sechs klugen Strategien."},
                    {"title": "Prüfen & Anpassen", "text": "Die Komposition vor der Ausgabe verfeinern."},
                    {"title": "Optimierte Ausgabe", "text": "Direkt anwenden oder pro Monitor exportieren."}
                ]},
                {"type": "shot", "title": "Zentrale Oberfläche", "text": "Ein effizientes Dashboard für alle Ihre Hintergründe.", "image": SCREEN_1, "caption_title": "Alles im Blick", "caption_text": "Vorschau und Ausgabesteuerung in einem Fenster."},
                {"type": "links", "title": "Weiterlesen", "text": "Entdecken Sie die Möglichkeiten von WallCraft Pro.", "links": ["download", "use-cases", "faq"]}
            ]
        },
        "dual-monitor-wallpaper-windows-11": {
            "meta_title": "Dual-Monitor unter Windows 11 ohne Zuschnitt",
            "meta_description": "Erstellen Sie perfekte Dual-Monitor-Hintergrundbilder unter Windows 11 ohne Zuschnitt oder Verzerrung.",
            "hero_title": "Wallpaper ohne Zuschnitt unter Windows 11",
            "hero_lead": "Standard-Wallpaper scheitern an gemischten Monitoren. WallCraft Pro löst dieses Problem.",
            "sections": [
                {"type": "text", "title": "Die Geometrie-Falle", "text": "Zwei Bildschirme bilden selten ein perfektes Rechteck.", "body": ["Ein Monitor kann höher sein oder hochkant stehen.", "Windows-Standardmodi verzerren oder schneiden Bilder hier oft ab."], "list": ["Unterschiedliche Höhen.", "Andere Formate.", "Abgeschnittene Motive."], "aside_title": "Die WallCraft-Lösung", "aside_body": ["Hält das Bild sichtbar statt es zu beschneiden.", "Passt sich der realen Anordnung des Schreibtischs an."]},
                {"type": "cards", "title": "Vorteile", "text": "Praktische Features für Multi-Monitor-User.", "cards": [
                    {"title": "Fit-Inside-Modus", "text": "Garantiert volle Bildsichtbarkeit."},
                    {"title": "Layout-Wahl", "text": "Wählen Sie die passende Strategie."},
                    {"title": "Sauberer Export", "text": "Ergebnisse passend pro Bildschirm speichern."}
                ]},
                {"type": "links", "title": "Mehr Anleitungen", "text": "Hilfe für andere Konfigurationen.", "links": ["download", "dual-monitor-wallpaper-without-cropping", "faq"]}
            ]
        },
        "faq": {
            "meta_title": "FAQ zu WallCraft Pro",
            "meta_description": "Häufig gestellte Fragen zu WallCraft Pro und Multi-Monitor-Wallpaper-Lösungen.",
            "hero_title": "Häufige Fragen zu WallCraft Pro",
            "hero_lead": "Antworten auf die wichtigsten Fragen zur Anwendung.",
            "sections": [
                {"type": "faq", "title": "FAQ WallCraft Pro", "text": "Detaillierte Fragen und Antworten.", "items": FAQ_ITEMS["de"]},
                {"type": "links", "title": "Wie geht es weiter?", "text": "App laden oder mit Alternativen vergleichen.", "links": ["download", "compare", "how-it-works"]}
            ]
        },
        "compare": {
            "meta_title": "WallCraft Pro im Vergleich",
            "meta_description": "Vergleichen Sie WallCraft Pro mit Windows, Wallpaper Engine und DisplayFusion für Ihr Multi-Monitor-Setup.",
            "hero_title": "WallCraft Pro und gängige Alternativen",
            "hero_lead": "Wählen Sie das richtige Tool für Ihre Multi-Monitor-Bedürfnisse.",
            "sections": [
                {"type": "compare", "title": "Anwendungsfälle", "text": "Jedes Tool hat seine Stärken. Sehen Sie, wo WallCraft punktet.", "headers": ["Option", "Am besten für", "Fokus", "Stärke von WallCraft"], "rows": [
                    ["WallCraft Pro", "Statische Wallpaper auf Mix-Desks", "Kein Zuschnitt, Aufteilung, nativ", "Erhält des ganzen Bildes"],
                    ["Windows-Optionen", "Einfache Wechsel", "Einfache native Verwaltung", "Zu simpel für Mix-Setups"],
                    ["Wallpaper Engine", "Animierte Hintergründe", "Interaktion und Community", "Weniger für statische Fotos optimiert"],
                    ["DisplayFusion", "Globale Desktop-Verwaltung", "Fenster-Handling & Produktivität", "Komplexer für reine Wallpaper"]
                ], "notes": [
                    {"title": "Wählen Sie Ihre Kategorie", "text": "WallCraft fokussiert auf statische Bilder für ungleiche Screens."},
                    {"title": "Gezielter Nutzen", "text": "Das Versprechen ist simpel: Bild sichtbar halten, Layout säubern."}
                ]},
                {"type": "links", "title": "Entscheidungszeit", "text": "Bereit zum Testen? Hier geht es weiter.", "links": ["download", "dual-monitor-wallpaper-windows-11", "mixed-monitor-wallpaper-setup"]}
            ]
        },
        "use-cases": {
            "meta_title": "Einsatzszenarien für WallCraft Pro",
            "meta_description": "Entdecken Sie Einsatzszenarien für WallCraft Pro bei Laptops, vertikalen Monitoren und Triple-Monitor-Setups.",
            "hero_title": "Echte Desks, echte Lösungen",
            "hero_lead": "Sehen Sie, wie WallCraft Pro mit verschiedenen Setups umgeht.",
            "sections": [
                {"type": "cards", "title": "Gängige Setups", "text": "Beispiele aus dem Alltag mit WallCraft Pro.", "cards": [
                    {"title": "Laptop & Monitor", "text": "Hilfreich, wenn ein Screen kleiner ist."},
                    {"title": "Vertikal & Breitbild", "text": "Wo normale Panoramen sofort scheitern."},
                    {"title": "Triple-Monitor-Station", "text": "Schafft eine kohärente Bilderwand auf drei Screens."},
                    {"title": "Verschiedene Höhen", "text": "Wichtig, wenn Kanten nicht fluchten."},
                    {"title": "Fokus auf Fotografie", "text": "Erhält das Bild ohne Zuschnitt."},
                    {"title": "Kunst & Illustration", "text": "Vermeidet störende Verzerrungen."}
                ]},
                {"type": "links", "title": "Mehr entdecken", "text": "Erfahren Sie, wie Sie diese Setups realisieren.", "links": ["download", "how-it-works", "dual-monitor-wallpaper-without-cropping"]}
            ]
        },
        "dual-monitor-wallpaper-without-cropping": {
            "meta_title": "Wallpaper ohne Zuschnitt erstellen",
            "meta_description": "Ein praktischer Leitfaden zum Erstellen von Hintergrundbildern ohne Zuschnitt auf zwei Monitoren.",
            "hero_title": "Wallpaper ohne Zuschnitt auf zwei Monitoren",
            "hero_lead": "Praktischer Leitfaden für unversehrte Bilder.",
            "sections": [
                {"type": "steps", "title": "No-Crop Workflow", "text": "Leerraum effektiv verwalten und Proportionen wahren.", "steps": [
                    {"title": "Wertvolle Quellbilder", "text": "Bilder wählen, bei denen der Rahmen zählt."},
                    {"title": "Fit-Inside nutzen", "text": "Hält Sichtbarkeit und Seitenverhältnis."},
                    {"title": "Layout wählen", "text": "Maximale Optimierung spart Platz."},
                    {"title": "Ausgabe teilen", "text": "Manuellen Zuschnitt in Editoren vermeiden."}
                ]},
                {"type": "text", "title": "Warum das zählt", "text": "Standardtools zerstören oft den Bildausschnitt.", "body": ["Den Ausschnitt zu bewahren, respektiert das Werk des Künstlers.", "Ideal für hochwertige Hintergründe und Fotoportfolios."], "list": ["Kein destruktiver Zuschnitt.", "Besserer Fit für Kunst.", "Direkter Weg zum Download."], "aside_title": "Info", "aside_body": ["Mehr als 80% der Multi-Monitor-User ärgern sich über falschen Bildbeschnitt."]},
                {"type": "links", "title": "Verwandte Themen", "text": "Weitere Multi-Monitor-Techniken entdecken.", "links": ["download", "mixed-monitor-wallpaper-setup", "faq"]}
            ]
        },
        "mixed-monitor-wallpaper-setup": {
            "meta_title": "Bestes Setup für unterschiedliche Monitore",
            "meta_description": "Erfahren Sie, wie Sie das beste Wallpaper-Setup für ungleichmäßige Monitore unter Windows konfigurieren.",
            "hero_title": "Das beste Wallpaper-Setup für gemischte Monitore",
            "hero_lead": "Ungleiche Geometrie ist die Stärke von WallCraft Pro.",
            "sections": [
                {"type": "text", "title": "Die Geometrie-Herausforderung", "text": "Höhenunterschiede ändern alles.", "body": ["Ein gutes Setup akzeptiert ungleiche Monitore.", "Der Workflow passt sich der Geometrie an, statt global zu schneiden."], "list": ["Mixed-Auflösungen.", "Unterschiedliche Bauhöhen.", "Variierende Formate."], "aside_title": "Der WallCraft-Ansatz", "aside_body": ["Behandelt die Monitor-Karte als Kern des Workflows.", "Ihre Wallpaper wirken wie maßgeschneidert für Ihren Desk."]},
                {"type": "cards", "title": "Optimierte Layouts", "text": "Wählen Sie den Algorithmus für Ihre Anordnung.", "cards": [
                    {"title": "Maximale Optimierung", "text": "Minimiert sichtbare Balken am effektivsten."},
                    {"title": "Justierte Linien", "text": "Ideal für einen rhythmischen Ausgleich."},
                    {"title": "Gitter & Streifen", "text": "Praktisch für klare visuelle Ordnung."}
                ]},
                {"type": "links", "title": "Nächster Schritt", "text": "Bereit für den Test?", "links": ["download", "dual-monitor-wallpaper-without-cropping", "use-cases"]}
            ]
        },
    },
    "fr": {
        "home": {
            "meta_title": "WallCraft Pro - Générateur de fond d'écran multi-écrans pour Windows 10/11",
            "meta_description": "Créez et appliquez des fonds d'écran sur des configurations double écran, triple écran et écrans de tailles différentes sous Windows 10/11, sans rognage ni déformation.",
            "hero_badge": "Conçu pour Windows 10 et 11",
            "hero_title": "Créer un fond d'écran propre pour des écrans de tailles différentes",
            "hero_lead": "WallCraft Pro aide à composer, découper et appliquer des fonds d'écran sur des configurations double écran, triple écran, verticales, ultrawide et multi-formats, sans rognage ni déformation.",
            "hero_points": [
                "Visibilité totale de l'image grâce au moteur fit-inside.",
                "Six modes de layout, dont l'optimisation maximale.",
                "Export, découpe par écran, ou application directe sur Windows."
            ],
            "hero_caption_title": "Capture réelle de l'interface actuelle",
            "hero_caption_text": "L'espace principal réunit l'aperçu, les layouts, la gestion des images et les sorties dans une seule application Windows.",
            "sections": [
                {"type": "cards", "title": "Guides et configurations spécifiques", "text": "Des ressources dédiées pour chaque type de configuration multi-écrans.", "cards": [
                    {"title": "Fond d'écran double écran Windows 11", "text": "Résoudre le cas classique du double écran sans crop forcé.", "page": "dual-monitor-wallpaper-windows-11"},
                    {"title": "Workflow sans rognage", "text": "Garder chaque photo visible, même sur des écrans irréguliers.", "page": "dual-monitor-wallpaper-without-cropping"},
                    {"title": "Moniteurs de tailles différentes", "text": "Gérer proprement résolutions, hauteurs et ratios différents.", "page": "mixed-monitor-wallpaper-setup"}
                ]},
                {"type": "steps", "title": "Comment fonctionne le workflow", "text": "WallCraft est une chaîne de composition complète pour vos fonds d'écran.", "steps": [
                    {"title": "Importer les photos", "text": "Construire le projet à partir de vraies images, pas d'un panorama figé."},
                    {"title": "Choisir un layout", "text": "Utiliser l'un des six algorithmes selon le setup."},
                    {"title": "Prévisualiser et ajuster", "text": "Vérifier la géométrie, réorganiser, retoucher."},
                    {"title": "Exporter, découper ou appliquer", "text": "Finir avec la sortie adaptée au bureau."}
                ]},
                {"type": "shot", "title": "Aperçu réel", "text": "Découvrez l'interface optimisée pour la gestion multi-écrans.", "image": SCREEN_2, "caption_title": "Aperçu de l'optimisation maximale", "caption_text": "Le layout heuristique calcule les meilleures permutations pour réduire le vide sur des écrans hétérogènes."},
                {"type": "faq", "title": "Questions fréquentes", "text": "Les réponses aux interrogations les plus courantes avant utilisation.", "items": FAQ_ITEMS["fr"][:4]},
                {"type": "links", "title": "Aller plus loin", "text": "Explorez toutes les facettes et fonctionnalités de l'utilisation de WallCraft Pro.", "links": ["download", "how-it-works", "use-cases", "compare", "faq"]}
            ]
        },
        "download": {
            "meta_title": "Télécharger WallCraft Pro v1.0.0 pour Windows 10/11",
            "meta_description": "Téléchargez WallCraft Pro v1.0.0 pour Windows 10/11, consultez le dépôt GitHub et lisez les notes de version depuis GitHub Releases.",
            "hero_badge": "GitHub Release v1.0.0",
            "hero_title": "Télécharger WallCraft Pro v1.0.0 pour Windows 10/11",
            "hero_lead": "Récupérez la première release Windows packagée de WallCraft Pro, consultez le code source et vérifiez les notes de version sur GitHub.",
            "sections": [
                {"type": "cards", "title": "Accès au produit", "text": "La v1.0.0 est disponible officiellement sur GitHub Releases.", "cards": [
                    {"title": "Release Windows officielle", "text": "Télécharger l'exécutable packagé pour Windows 10/11.", "url": DOWNLOAD_URL, "cta": f"Télécharger v{PRODUCT_VERSION} pour Windows"},
                    {"title": "Code source", "text": "Inspecter le dépôt, mettre une étoile ou compiler depuis la source.", "url": REPO_URL, "cta": "Voir sur GitHub"},
                    {"title": "Notes de version", "text": "Ouvrir GitHub Releases pour l'historique des versions.", "url": RELEASES_URL, "cta": "Ouvrir les releases GitHub"}
                ]},
                {"type": "text", "title": "Détails de la release", "text": "WallCraft est maintenant disponible en version stable pour tous les utilisateurs Windows.", "body": ["Le package public actuel est la v1.0.0 pour Windows.", "La page GitHub Releases contient les journaux de modifications."], "list": ["Exécutable Windows 10/11 disponible maintenant.", "Le dépôt open source reste public.", "L'historique démarre désormais avec la v1.0.0."], "aside_title": "Version actuelle", "aside_body": ["Fichier : WallCraft-Pro-v1.0.0-Windows.exe.", "Les notes de version et builds futurs vivent sur GitHub."]},
                {"type": "shot", "title": "Aperçu visuel", "text": "Vérifiez l'interface de l'application avant de télécharger.", "image": SCREEN_1, "caption_title": "Espace de travail", "caption_text": "L'interface regroupe aperçu, layouts, édition et sorties dans une vue unique."},
                {"type": "links", "title": "Autres ressources", "text": "Des pages pour vous aider à démarrer.", "links": ["how-it-works", "faq", "compare"]}
            ]
        },
        "how-it-works": {
            "meta_title": "Comment WallCraft Pro fonctionne sur des écrans de tailles différentes",
            "meta_description": "Découvrez comment WallCraft Pro détecte les écrans, préserve la visibilité des images, choisit les layouts et exporte ou applique les fonds d'écran multi-écrans.",
            "hero_badge": "Visite produit",
            "hero_title": "Comment WallCraft compose un fond d'écran pour des écrans irréguliers",
            "hero_lead": "Découvrez le workflow précis qui garantit un résultat parfait sur vos moniteurs.",
            "sections": [
                {"type": "steps", "title": "Cinq étapes du dossier photo au bureau", "text": "La logique interne de WallCraft résout les défis géométriques complexes.", "steps": [
                    {"title": "Détecter la vraie carte des écrans", "text": "WallCraft lit la disposition physique des moniteurs."},
                    {"title": "Garder chaque image dans son cadre", "text": "Le fit-inside protège le ratio d'origine et évite le rognage."},
                    {"title": "Lancer un algorithme de layout", "text": "Choisir parmi six stratégies."},
                    {"title": "Prévisualiser et ajuster", "text": "Ajuster la composition avant la sortie."},
                    {"title": "Exporter, découper ou appliquer", "text": "Utiliser la sortie adaptée au bureau."}
                ]},
                {"type": "shot", "title": "Interface unifiée", "text": "Un tableau de bord efficace pour toutes vos tâches de fond d'écran.", "image": SCREEN_1, "caption_title": "Aperçu et sorties réunis", "caption_text": "L'application évite les allers-retours entre différents outils."},
                {"type": "links", "title": "Pages suivantes", "text": "Continuez l'exploration de WallCraft Pro.", "links": ["download", "use-cases", "faq"]}
            ]
        },
        "dual-monitor-wallpaper-windows-11": {
            "meta_title": "Fond d'écran double écran sur Windows 11 sans rognage",
            "meta_description": "Créez un fond d'écran double écran sur Windows 11 sans rognage ni déformation, même avec des moniteurs de tailles ou d'alignements différents.",
            "hero_badge": "Guide d'optimisation",
            "hero_title": "Créer un fond d'écran double écran sur Windows 11 sans rognage",
            "hero_lead": "Les réglages Windows standard échouent souvent sur le double écran mixte. WallCraft Pro est la solution.",
            "sections": [
                {"type": "text", "title": "Le problème du double écran hétérogène", "text": "Deux écrans ne partagent quasiment jamais un rectangle parfait.", "body": ["Un écran peut être plus haut, décalé ou vertical.", "C'est pour cela que les réglages 'Remplir' ou 'Étendre' sont souvent frustrants."], "list": ["Hauteurs différentes.", "Ratios différents.", "Sujet coupé par les bordures."], "aside_title": "L'approche WallCraft", "aside_body": ["WallCraft conserve l'image entière au lieu de forcer un crop destructif.", "Il s'adapté à la géométrie réelle de votre bureau."]},
                {"type": "cards", "title": "Avantages clés", "text": "Des fonctionnalités pratiques pour les utilisateurs multi-écrans.", "cards": [
                    {"title": "Placement fit-inside", "text": "Garder l'image entière visible au lieu de la couper."},
                    {"title": "Choix du layout", "text": "Choisir une stratégie adaptée au bureau."},
                    {"title": "Sortie par écran", "text": "Exporter et découper proprement le résultat."}
                ]},
                {"type": "links", "title": "En savoir plus", "text": "Guides spécifiques pour d'autres configurations.", "links": ["download", "dual-monitor-wallpaper-without-cropping", "faq"]}
            ]
        },
        "faq": {
            "meta_title": "FAQ WallCraft Pro",
            "meta_description": "Consultez la FAQ WallCraft Pro sur le rognage, les écrans de tailles différentes, le support Windows, l'export découpé, l'open source et l'état du téléchargement.",
            "hero_badge": "Support & Documentation",
            "hero_title": "Questions fréquentes sur WallCraft Pro",
            "hero_lead": "Retrouvez ici les réponses aux questions les plus posées sur l'application.",
            "sections": [
                {"type": "faq", "title": "FAQ WallCraft Pro", "text": "Questions communes et réponses détaillées.", "items": FAQ_ITEMS["fr"]},
                {"type": "links", "title": "La suite", "text": "Téléchargez l'application ou comparez avec d'autres outils.", "links": ["download", "compare", "how-it-works"]}
            ]
        },
        "compare": {
            "meta_title": "Comparer WallCraft Pro avec d'autres solutions de fond d'écran",
            "meta_description": "Comparez WallCraft Pro avec les réglages Windows, Wallpaper Engine et DisplayFusion pour choisir le bon outil selon votre besoin multi-écrans.",
            "hero_badge": "Guide comparatif",
            "hero_title": "Comparer WallCraft Pro avec les alternatives courantes",
            "hero_lead": "Choisissez l'outil adapté à vos besoins multi-écrans spécifiques.",
            "sections": [
                {"type": "compare", "title": "Positionnement par cas d'usage", "text": "Chaque outil a ses forces. Découvrez où WallCraft Pro excelle.", "headers": ["Option", "Meilleur usage", "Focus principal", "Force de WallCraft"], "rows": [
                    ["WallCraft Pro", "Fonds statiques sur écrans hétérogènes", "Pas de rognage, découpe, application native", "Conçu pour préserver l'image entière"],
                    ["Réglages Windows", "Changements basiques de fond", "Thèmes et gestion native simple", "Limité pour les configurations complexes"],
                    ["Wallpaper Engine", "Fonds animés ou interactifs", "Mouvement et contenu communautaire", "Moins adapté à la composition photo statique"],
                    ["DisplayFusion", "Gestion globale du bureau multi-écrans", "Fenêtrès, outils moniteurs et productivité", "Plus complexe pour la simple composition de fonds"]
                ], "notes": [
                    {"title": "Choisir sa catégorie", "text": "WallCraft se concentre sur l'image statique pour écrans irréguliers."},
                    {"title": "Utilité ciblée", "text": "La promesse est simple : garder l'image visible et rendre le setup propre."}
                ]},
                {"type": "links", "title": "Votre décision", "text": "Prêt à choisir ? Consultez les sections pertinentes.", "links": ["download", "dual-monitor-wallpaper-windows-11", "mixed-monitor-wallpaper-setup"]}
            ]
        },
        "use-cases": {
            "meta_title": "Cas d'usage WallCraft Pro pour double écran, triple écran et moniteurs mixtes",
            "meta_description": "Explorez les cas d'usage WallCraft Pro pour le double écran, le triple écran, le portable avec écran externe, l'ultrawide et les moniteurs de tailles différentes.",
            "hero_badge": "Scénarios utilisateurs",
            "hero_title": "Bureaux réels, solutions concrètes",
            "hero_lead": "Découvrez comment WallCraft Pro s'adapté à diverses configurations.",
            "sections": [
                {"type": "cards", "title": "Configurations courantes", "text": "Exemples d'utilisation de WallCraft Pro au quotidien.", "cards": [
                    {"title": "Portable plus écran externe", "text": "Utile quand un écran est plus petit ou décalé."},
                    {"title": "Vertical plus ultrawide", "text": "Une disposition créative où les panoramas ordinaires cassent immédiatement."},
                    {"title": "Station triple écran", "text": "Pratique pour créer un mur d'images cohérent sur trois moniteurs."},
                    {"title": "Hauteurs d'écrans différentes", "text": "Important quand les bords des écrans ne s'alignent pas physiquement."},
                    {"title": "Bureaux orientés photo", "text": "Pertinent quand préserver l'image complète compte vraiment."},
                    {"title": "Illustration et art", "text": "Bon choix quand la déformation serait pire que quelques bandes."}
                ]},
                {"type": "links", "title": "En savoir plus", "text": "Apprenez comment réaliser ces configurations chez vous.", "links": ["download", "how-it-works", "dual-monitor-wallpaper-without-cropping"]}
            ]
        },
        "dual-monitor-wallpaper-without-cropping": {
            "meta_title": "Comment faire un fond d'écran double écran sans rognage",
            "meta_description": "Apprenez à créer un fond d'écran double écran sans rognage grâce au placement fit-inside, aux stratégies de layout et à l'export par écran.",
            "hero_badge": "Guide pas-à-pas",
            "hero_title": "Comment faire un fond d'écran double écran sans rognage",
            "hero_lead": "Un guide pratique pour conserver l'intégrité de vos images sur plusieurs écrans.",
            "sections": [
                {"type": "steps", "title": "Un workflow sans rognage fiable", "text": "Gérez l'espace vide efficacement tout en respectant les proportions d'origine.", "steps": [
                    {"title": "Partir d'images à préserver", "text": "Choisir des images où garder le cadre entier compte vraiment."},
                    {"title": "Utiliser fit-inside", "text": "Conserver l'image visible et le ratio d'origine."},
                    {"title": "Choisir le bon layout", "text": "L'optimisation maximale réduit souvent les bandes visibles."},
                    {"title": "Découper la sortie par écran", "text": "Éviter la découpe manuelle dans un autre logiciel."}
                ]},
                {"type": "text", "title": "Pourquoi c'est important", "text": "Les outils standards forcent souvent un crop destructif sur vos photos préférées.", "body": ["Éviter le crop permet de respecter l'intention originale de l'artiste ou du photographe.", "C'est l'outil idéal pour les fonds d'écran de haute qualité et les portfolios."], "list": ["Pas de crop destructif.", "Meilleur fit pour photo et illustration.", "Pont naturel vers téléchargement et FAQ."]},
                {"type": "links", "title": "Voir aussi", "text": "Continuez à explorer les techniques de fond d'écran multi-écrans.", "links": ["download", "mixed-monitor-wallpaper-setup", "faq"]}
            ]
        },
        "mixed-monitor-wallpaper-setup": {
            "meta_title": "Meilleure configuration de fond d'écran pour des moniteurs de tailles différentes",
            "meta_description": "Trouvez la meilleure configuration de fond d'écran pour des moniteurs de tailles différentes, de hauteurs différentes et des bureaux irréguliers sous Windows 10/11.",
            "hero_badge": "Guide avancé",
            "hero_title": "La meilleure approche pour les écrans de tailles différentes",
            "hero_lead": "La gestion de la géométrie irrégulière est la force de WallCraft Pro.",
            "sections": [
                {"type": "text", "title": "Le défi de la géométrie", "text": "Un écran plus haut ou vertical change tout.", "body": ["Une bonne configuration assume que les moniteurs ne forment pas un rectangle parfait.", "Le workflow s'adapté à cette géométrie au lieu de forcer un crop global."], "list": ["Résolutions différentes.", "Hauteurs physiques différentes.", "Ratios différents."], "aside_title": "Ce que WallCraft apporte", "aside_body": ["Il traite la carte des écrans comme un élément central du workflow.", "Vos fonds d'écran paraissent être créés sur mesure pour votre bureau."]},
                {"type": "cards", "title": "Layouts optimisés", "text": "Choisissez l'algorithme qui correspond le mieux à votre disposition.", "cards": [
                    {"title": "Optimisation maximale", "text": "Le meilleur choix pour réduire les bandes visibles."},
                    {"title": "Lignes justifiées", "text": "Idéal pour un rythme visuel équilibré."},
                    {"title": "Grilles et bandes", "text": "Pratique quand l'ordre visuel prime sur le remplissage."}
                ]},
                {"type": "links", "title": "Prêt à tester ?", "text": "Passez à l'étape suivante.", "links": ["download", "dual-monitor-wallpaper-without-cropping", "use-cases"]}
            ]
        },
    },
}

SITE_REFRESH_EN = {
    "home": {
        "meta_title": f"WallCraft Pro {PRODUCT_VERSION} - Multi-Monitor Wallpaper Generator for Windows 10/11",
        "meta_description": "WallCraft Pro 2026.3.14 adds a redesigned workspace, manual scale mode, layer ordering, new project reset, and a cleaner live output preview for multi-monitor wallpapers.",
        "hero_badge": f"Product refresh {PRODUCT_VERSION}",
        "hero_title": "Design wallpapers visually for real multi-monitor desks",
        "hero_lead": "The 2026.3.14 update brings a cleaner workspace, manual proportional scaling, front/back layer control, new project reset, and a more realistic live output preview.",
        "hero_points": [
            "Move, scale, crop, and reorder images from one streamlined workspace.",
            "Preview the result on realistic dark monitor frames before applying it.",
            "Keep every image visible across dual, triple, and mixed-size setups."
        ],
        "hero_caption_title": f"WallCraft {PRODUCT_VERSION} workspace",
        "hero_caption_text": "The refreshed interface focuses on composition, quick actions, and live monitor feedback.",
        "sections": [
            {"type": "cards", "title": f"What's new in {PRODUCT_VERSION}", "text": "The latest app refresh is focused on usability and visual editing speed.", "cards": [
                {"title": "Redesigned workspace", "text": "A clearer top toolbar, a larger composition stage, and a more focused imported-images panel."},
                {"title": "Manual scale mode", "text": "Enlarge or reduce a photo manually while preserving its aspect ratio."},
                {"title": "Layer order controls", "text": "Push an image backward or bring it forward directly from the library."},
                {"title": "New project reset", "text": "Start over instantly without manually clearing every imported asset."}
            ]},
            {"type": "shot", "title": "Modern live workspace", "text": "The latest build centers the composition stage and makes the editing workflow more obvious at a glance.", "image": SCREEN_1, "caption_title": "Redesigned 2026.3.14 interface", "caption_text": "Project actions, layout choice, language, and edit modes now sit in a more natural order."},
            {"type": "shot", "title": "Cleaner output preview", "text": "The monitor preview now looks closer to a real desk setup, with darker frames and more breathing room between screens.", "image": SCREEN_2, "caption_title": "Realistic output preview", "caption_text": "Preview the wallpaper on simplified black displays before exporting or applying it."},
            {"type": "steps", "title": "How the workflow feels now", "text": "The latest version keeps the product simple from import to desktop.", "steps": [
                {"title": "Import images", "text": "Bring one or more photos into the project library."},
                {"title": "Choose a layout", "text": "Use one of the built-in arrangements or auto-organize the scene."},
                {"title": "Move, scale, crop", "text": "Adjust each image on the stage with dedicated edit modes."},
                {"title": "Change layer order", "text": "Send an image backward or forward when overlaps matter."},
                {"title": "Preview and apply", "text": "Check the live monitor view, then export, split, or apply on Windows."}
            ]},
            {"type": "cards", "title": "Keep exploring", "text": "The new UI sits on top of the same no-crop, mixed-monitor workflow.", "cards": [
                {"title": "Dual monitor wallpaper on Windows 11", "text": "Fix the common dual-monitor wallpaper problem without forced cropping.", "page": "dual-monitor-wallpaper-windows-11"},
                {"title": "No crop workflow", "text": "Keep every photo visible, even across uneven screens.", "page": "dual-monitor-wallpaper-without-cropping"},
                {"title": "Mixed monitor sizes", "text": "Handle different resolutions, heights, and aspect ratios cleanly.", "page": "mixed-monitor-wallpaper-setup"}
            ]},
            {"type": "faq", "title": "Questions before download", "text": "Quick answers about the new editing workflow and the product itself.", "items": FAQ_ITEMS["en"][:4]},
            {"type": "links", "title": "Learn more about WallCraft Pro", "text": "Explore the download page, workflow details, and use cases.", "links": ["download", "how-it-works", "use-cases", "faq", "compare"]}
        ],
    },
    "download": {
        "meta_title": f"Download WallCraft Pro for Windows 10/11 - {PRODUCT_VERSION} site update",
        "meta_description": "Download WallCraft Pro for Windows 10/11 and see what changed in the 2026.3.14 site and interface refresh: redesigned workspace, manual scaling, layer order, and realistic output preview.",
        "hero_badge": f"Website & UI refresh {PRODUCT_VERSION}",
        "hero_title": "Download WallCraft Pro for Windows 10/11",
        "hero_lead": "The website now reflects the 2026.3.14 product refresh. The Windows executable is distributed through GitHub Releases, with the latest screenshots and feature overview below.",
        "sections": [
            {"type": "cards", "title": "Choose your path", "text": "Download the Windows build, inspect the source code, or open GitHub Releases.", "cards": [
                {"title": "Current Windows download", "text": "Get the packaged executable for Windows 10/11 from GitHub.", "url": DOWNLOAD_URL, "cta": f"Download v{PRODUCT_VERSION} for Windows"},
                {"title": "Source code", "text": "Inspect the repository, follow development, or build from source.", "url": REPO_URL, "cta": "View on GitHub"},
                {"title": "GitHub Releases", "text": "Open the public release page and keep an eye on packaged updates.", "url": RELEASES_URL, "cta": "Open GitHub releases"}
            ]},
            {"type": "text", "title": f"What changed in {PRODUCT_VERSION}", "text": "This refresh is mostly about workflow quality and readability.", "body": [
                "The interface now gives more space to the composition stage and removes the old inspector-heavy layout.",
                "Editing is clearer with separate move, scale, and crop modes plus front/back layer controls."
            ], "list": [
                "Manual image scaling with preserved aspect ratio.",
                "Front/back image ordering from the library.",
                "New project reset button.",
                "Cleaner and more realistic output preview."
            ], "aside_title": "About the download", "aside_body": [
                "The public Windows executable is hosted on GitHub Releases.",
                "The website and screenshots have been updated to match the 2026.3.14 application refresh."
            ]},
            {"type": "shot", "title": "Current application workspace", "text": "See the refreshed interface before downloading it.", "image": SCREEN_1, "caption_title": "Full workspace view", "caption_text": "Project actions, layout selection, edit modes, composition stage, and output preview are now better organized."},
            {"type": "shot", "title": "Live monitor preview", "text": "The output preview now sells the result more clearly and helps validate a composition before applying it.", "image": SCREEN_2, "caption_title": "Live output scene", "caption_text": "Dark monitor frames and wider spacing make the preview easier to read at a glance."},
            {"type": "links", "title": "Other useful resources", "text": "Continue with the workflow guide, use cases, or FAQ.", "links": ["how-it-works", "use-cases", "faq", "compare"]}
        ],
    },
    "how-it-works": {
        "meta_title": f"How WallCraft Pro Works - {PRODUCT_VERSION} workflow refresh",
        "meta_description": "See how WallCraft Pro imports images, scales them manually, changes layer order, previews mixed-monitor results, and applies wallpapers on Windows.",
        "hero_badge": "Workflow walkthrough",
        "hero_title": "How the refreshed WallCraft workflow works",
        "hero_lead": "The interface is built around a simpler editing loop: import, arrange, scale, reorder, preview, and apply.",
        "sections": [
            {"type": "steps", "title": "Five steps from images to desktop", "text": "The current workflow is faster to understand and easier to control.", "steps": [
                {"title": "Import your images", "text": "Load one or more photos into the project library."},
                {"title": "Build the composition", "text": "Place the images inside the virtual desktop and choose a layout strategy."},
                {"title": "Scale without distortion", "text": "Use the dedicated scale mode to resize a photo while preserving its ratio."},
                {"title": "Adjust the visual stack", "text": "Send an image backward or bring it forward when elements overlap."},
                {"title": "Preview on monitors and apply", "text": "Use the realistic output preview, then export, split, or apply on Windows."}
            ]},
            {"type": "shot", "title": "The current workspace", "text": "The new layout keeps the most important actions at the top and the stage in the center.", "image": SCREEN_1, "caption_title": "Workspace refresh", "caption_text": "The new project button, compact library, and edit modes make the tool easier to use from the first launch."},
            {"type": "shot", "title": "Composition stage details", "text": "The editing stage is larger and clearer, with direct monitor feedback and obvious handles.", "image": SCREEN_3, "caption_title": "Stage and scaling handles", "caption_text": "Scale, crop, and move images directly on the virtual desktop while checking the real monitor map."},
            {"type": "cards", "title": "Why the new workflow matters", "text": "The refresh makes WallCraft feel more like a focused design utility than a technical tool.", "cards": [
                {"title": "Less clutter", "text": "The old inspector area is gone so the stage can breathe."},
                {"title": "Better editing signals", "text": "Mode-specific controls and handles explain what will happen next."},
                {"title": "Stronger visual proof", "text": "The output preview now communicates the result more clearly."}
            ]},
            {"type": "links", "title": "Continue your tour", "text": "Download the app or jump into specific desk setups.", "links": ["download", "use-cases", "dual-monitor-wallpaper-windows-11", "faq"]}
        ],
    },
}

SITE_REFRESH_FR = {
    "home": {
        "meta_title": f"WallCraft Pro {PRODUCT_VERSION} - Générateur de fond d'écran multi-écrans pour Windows 10/11",
        "meta_description": "WallCraft Pro 2026.3.14 apporte un workspace repensé, le redimensionnement manuel proportionnel, l'ordre avant/arrière, le reset de projet et un aperçu de sortie plus réaliste.",
        "hero_badge": f"Mise à jour produit {PRODUCT_VERSION}",
        "hero_title": "Composer un fond d'écran visuellement pour de vrais bureaux multi-écrans",
        "hero_lead": "La mise à jour 2026.3.14 introduit un workspace plus clair, un mode de redimensionnement proportionnel, le contrôle des calques avant/arrière, un bouton nouveau projet et un aperçu de sortie plus réaliste.",
        "hero_points": [
            "Déplacer, redimensionner, rogner et réordonner les images depuis un seul workspace.",
            "Vérifier le rendu sur des écrans noirs plus crédibles avant d'appliquer.",
            "Garder l'image visible sur des setups double écran, triple écran et multi-formats."
        ],
        "hero_caption_title": f"Workspace WallCraft {PRODUCT_VERSION}",
        "hero_caption_text": "L'interface rafraîchie donne la priorité à la composition, aux actions rapides et au retour visuel en direct.",
        "sections": [
            {"type": "cards", "title": f"Nouveautes de {PRODUCT_VERSION}", "text": "Cette mise à jour se concentre sur l'ergonomie et l'édition visuelle.", "cards": [
                {"title": "Workspace repensé", "text": "Une toolbar plus claire, une zone de composition plus grande et une colonne images plus compacte."},
                {"title": "Mode redimensionner", "text": "Agrandir ou réduire une photo manuellement sans casser son ratio."},
                {"title": "Ordre des calques", "text": "Passer une image en arrière ou en avant directement depuis la bibliothèque."},
                {"title": "Nouveau projet", "text": "Repartir à zéro en un clic sans vider chaque image à la main."}
            ]},
            {"type": "shot", "title": "Nouveau workspace moderne", "text": "La version actuelle recentre l'application sur la composition et rend le workflow beaucoup plus lisible.", "image": SCREEN_1, "caption_title": "Interface 2026.3.14", "caption_text": "La nouvelle toolbar regroupe projet, langue, layout, modes d'édition et application du fond dans un ordre plus naturel."},
            {"type": "shot", "title": "Aperçu de sortie redesigné", "text": "L'aperçu de sortie est plus propre, plus sobre et plus proche d'un vrai setup de bureau.", "image": SCREEN_2, "caption_title": "Aperçu multi-écrans", "caption_text": "Des moniteurs noirs plus epures et mieux espaces rendent la verification plus rapide."},
            {"type": "steps", "title": "Le workflow maintenant", "text": "La nouvelle version garde le produit simple du dossier photo jusqu'au bureau Windows.", "steps": [
                {"title": "Importer les images", "text": "Charger une ou plusieurs photos dans la bibliothèque du projet."},
                {"title": "Choisir un layout", "text": "Utiliser un agencement intégré ou lancer l'auto-organisation."},
                {"title": "Déplacer, redimensionner, rogner", "text": "Ajuster chaque image sur la scène avec des modes d'édition dedies."},
                {"title": "Changer l'ordre visuel", "text": "Envoyer une image en arrière ou en avant quand des éléments se chevauchent."},
                {"title": "Prévisualiser et appliquer", "text": "Vérifier le rendu, puis exporter, découper ou appliquer sur Windows."}
            ]},
            {"type": "cards", "title": "Continuer l'exploration", "text": "La mise à jour ergonomique repose toujours sur le même moteur sans rognage pour les écrans hétérogènes.", "cards": [
                {"title": "Fond d'écran double écran Windows 11", "text": "Résoudre le cas classique du double écran sans crop force.", "page": "dual-monitor-wallpaper-windows-11"},
                {"title": "Workflow sans rognage", "text": "Garder chaque photo visible, même sur des écrans irréguliers.", "page": "dual-monitor-wallpaper-without-cropping"},
                {"title": "Moniteurs de tailles différentes", "text": "Gérer proprement résolutions, hauteurs et ratios différents.", "page": "mixed-monitor-wallpaper-setup"}
            ]},
            {"type": "faq", "title": "Questions avant téléchargement", "text": "Reponses rapides sur le nouveau workflow et les fonctions essentielles.", "items": FAQ_ITEMS["fr"][:4]},
            {"type": "links", "title": "Aller plus loin", "text": "Explorez le téléchargement, le fonctionnement et les cas d'usage.", "links": ["download", "how-it-works", "use-cases", "faq", "compare"]}
        ],
    },
    "download": {
        "meta_title": f"Télécharger WallCraft Pro pour Windows 10/11 - mise à jour {PRODUCT_VERSION}",
        "meta_description": "Téléchargez WallCraft Pro pour Windows 10/11 et découvrez la mise à jour 2026.3.14 du site et de l'interface: workspace repensé, scale proportionnel, ordre des calques et nouvel aperçu.",
        "hero_badge": f"Rafraichissement site & UI {PRODUCT_VERSION}",
        "hero_title": "Télécharger WallCraft Pro pour Windows 10/11",
        "hero_lead": "Le site reflète maintenant la mise à jour 2026.3.14 du produit. L'exécutable Windows reste distribué via GitHub Releases, avec de nouvelles captures et un meilleur résumé des fonctions.",
        "sections": [
            {"type": "cards", "title": "Choisissez votre acces", "text": "Téléchargez le build Windows, consultez le code source ou ouvrez GitHub Releases.", "cards": [
                {"title": "Téléchargement Windows actuel", "text": "Récupérer l'exécutable packagé pour Windows 10/11 depuis GitHub.", "url": DOWNLOAD_URL, "cta": f"Télécharger v{PRODUCT_VERSION} pour Windows"},
                {"title": "Code source", "text": "Inspecter le dépôt, suivre le développement ou compiler depuis la source.", "url": REPO_URL, "cta": "Voir sur GitHub"},
                {"title": "GitHub Releases", "text": "Ouvrir la page publique des releases et suivre les builds packages.", "url": RELEASES_URL, "cta": "Ouvrir les releases GitHub"}
            ]},
            {"type": "text", "title": f"Ce qui change dans {PRODUCT_VERSION}", "text": "Cette mise à jour porte surtout sur le confort du workflow et la lisibilite.", "body": [
                "L'interface donne plus de place à la scène de composition et supprime l'ancienne logique trop centrée sur l'inspecteur.",
                "L'édition est plus claire avec des modes separes pour déplacer, redimensionner et rogner, plus des controles de calques."
            ], "list": [
                "Redimensionnement manuel d'une image avec ratio conserve.",
                "Ordre avant/arrière depuis la bibliothèque.",
                "Bouton nouveau projet.",
                "Aperçu de sortie plus propre et plus réaliste."
            ], "aside_title": "A propos du téléchargement", "aside_body": [
                "L'exécutable Windows public reste heberge sur GitHub Releases.",
                "Le site et les captures ont été mis à jour pour correspondre à la refresh applicative 2026.3.14."
            ]},
            {"type": "shot", "title": "Workspace actuel", "text": "Consultez l'interface refaite avant de télécharger l'application.", "image": SCREEN_1, "caption_title": "Vue complète du workspace", "caption_text": "Projet, layouts, modes d'édition, scène de composition et aperçu de sortie sont mieux organises."},
            {"type": "shot", "title": "Aperçu live des écrans", "text": "Le nouvel aperçu vend mieux le résultat final et aide à valider une composition avant application.", "image": SCREEN_2, "caption_title": "Scène de sortie live", "caption_text": "Des écrans noirs plus sobes et plus espaces rendent la lecture plus immediate."},
            {"type": "links", "title": "Autres ressources utiles", "text": "Continuez avec le guide de fonctionnement, les cas d'usage ou la FAQ.", "links": ["how-it-works", "use-cases", "faq", "compare"]}
        ],
    },
    "how-it-works": {
        "meta_title": f"Comment fonctionne WallCraft Pro - refresh workflow {PRODUCT_VERSION}",
        "meta_description": "Découvrez comment WallCraft Pro importe les images, les redimensionne, gère l'ordre des calques, prévisualise le rendu multi-écrans et applique le fond sous Windows.",
        "hero_badge": "Visite du workflow",
        "hero_title": "Comment fonctionne le workflow repensé de WallCraft",
        "hero_lead": "L'interface est construite autour d'une boucle plus simple: importer, arranger, redimensionner, réordonner, prévisualiser et appliquer.",
        "sections": [
            {"type": "steps", "title": "Cinq étapes des images au bureau", "text": "Le workflow actuel est plus rapide à comprendre et plus simple à piloter.", "steps": [
                {"title": "Importer les images", "text": "Charger une ou plusieurs photos dans la bibliothèque du projet."},
                {"title": "Construire la composition", "text": "Placer les images dans le bureau virtuel et choisir une stratégie de layout."},
                {"title": "Redimensionner sans déformation", "text": "Utiliser le mode dédié pour changer la taille d'une photo tout en gardant son ratio."},
                {"title": "Ajuster l'empilement", "text": "Envoyer une image en arrière ou en avant quand des éléments se chevauchent."},
                {"title": "Prévisualiser et appliquer", "text": "Vérifier le rendu multi-écrans puis exporter, découper ou appliquer sous Windows."}
            ]},
            {"type": "shot", "title": "Le workspace actuel", "text": "Le nouveau layout garde les actions importantes en haut et la scène au centre.", "image": SCREEN_1, "caption_title": "Workspace refresh", "caption_text": "Le bouton nouveau projet, les modes d'édition et la bibliothèque compacte rendent l'app plus immediate."},
            {"type": "shot", "title": "Détails de la scène", "text": "La scène de composition est plus grande, plus lisible et plus directe à manipuler.", "image": SCREEN_3, "caption_title": "Scène et poignées de scale", "caption_text": "Redimensionnez, rognez et déplacez les images directement sur la carte virtuelle des écrans."},
            {"type": "cards", "title": "Pourquoi ce refresh compte", "text": "La mise à jour fait davantage ressembler WallCraft à un vrai outil de composition qu'à une interface technique.", "cards": [
                {"title": "Moins de bruit visuel", "text": "L'ancien panneau inspecteur a disparu au profit de la scène."},
                {"title": "Edition plus explicite", "text": "Les modes et poignées rendent chaque action plus evidente."},
                {"title": "Preuve visuelle plus forte", "text": "Le nouvel aperçu de sortie communique mieux le résultat final."}
            ]},
            {"type": "links", "title": "Continuer la visite", "text": "Téléchargez l'application ou explorez des setups plus précis.", "links": ["download", "use-cases", "dual-monitor-wallpaper-windows-11", "faq"]}
        ],
    },
}

SITE_REFRESH_ES = {
    "home": {
        "meta_title": f"WallCraft Pro {PRODUCT_VERSION} - Generador de fondos para varios monitores en Windows 10/11",
        "meta_description": "WallCraft Pro 2026.3.14 trae un workspace renovado, escala manual proporcional, orden de capas, nuevo proyecto y una vista de salida más limpia.",
        "hero_badge": f"Actualización del producto {PRODUCT_VERSION}",
        "hero_title": "Disenar fondos para escritorios multi-monitor reales",
        "hero_lead": "La actualización 2026.3.14 añade una interfaz más clara, escala manual con proporción fija, control delante/detrás y una vista previa de salida más realista.",
        "hero_points": [
            "Mover, escalar, recortar y reordenar imágenes desde un solo workspace.",
            "Previsualizar el resultado en monitores oscuros más realistas.",
            "Mantener la imagen visible en setups dobles, triples y mixtos."
        ],
        "hero_caption_title": f"Workspace de WallCraft {PRODUCT_VERSION}",
        "hero_caption_text": "La interfaz renovada da prioridad a la composición, a las acciones rapidas y a la vista previa en tiempo real.",
        "sections": [
            {"type": "cards", "title": f"Novedades de {PRODUCT_VERSION}", "text": "La actualización se centra en usabilidad y edición visual.", "cards": [
                {"title": "Workspace renovado", "text": "Toolbar más clara, escenario más grande y panel de imágenes más compacto."},
                {"title": "Modo escala", "text": "Agrandar o reducir una foto sin romper su proporción."},
                {"title": "Orden de capas", "text": "Enviar una imagen atras o delante desde la biblioteca."},
                {"title": "Nuevo proyecto", "text": "Empezar desde cero con un solo clic."}
            ]},
            {"type": "shot", "title": "Workspace moderno", "text": "La versión actual centra la aplicación en la composición y mejora la legibilidad.", "image": SCREEN_1, "caption_title": "Interfaz 2026.3.14", "caption_text": "La nueva toolbar organiza idioma, proyecto, layout, modos de edición y aplicación del fondo."},
            {"type": "shot", "title": "Vista previa de salida", "text": "La nueva vista previa es más sobria y más cercana a un escritorio real.", "image": SCREEN_2, "caption_title": "Preview multi-monitor", "caption_text": "Monitores oscuros y más separados facilitan la validación visual."},
            {"type": "links", "title": "Explorar más", "text": "Descubre la descarga, el funcionamiento y los casos de uso.", "links": ["download", "how-it-works", "use-cases", "faq", "compare"]}
        ],
    },
    "download": {
        "meta_title": f"Descargar WallCraft Pro para Windows 10/11 - actualización {PRODUCT_VERSION}",
        "meta_description": "Descarga WallCraft Pro para Windows 10/11 y descubre la actualización 2026.3.14 del sitio y de la interfaz.",
        "hero_badge": f"Refresh del sitio y UI {PRODUCT_VERSION}",
        "hero_title": "Descargar WallCraft Pro para Windows 10/11",
        "hero_lead": "El sitio refleja ahora la actualización 2026.3.14 del producto. El ejecutable de Windows sigue disponible en GitHub Releases.",
        "sections": [
            {"type": "cards", "title": "Elige tu acceso", "text": "Descarga la build de Windows, abre el código fuente o revisa GitHub Releases.", "cards": [
                {"title": "Descarga actual de Windows", "text": "Obtener el ejecutable empaquetado desde GitHub.", "url": DOWNLOAD_URL, "cta": f"Descargar v{PRODUCT_VERSION} para Windows"},
                {"title": "Código fuente", "text": "Inspeccionar el repositorio o compilar desde la fuente.", "url": REPO_URL, "cta": "Ver en GitHub"},
                {"title": "GitHub Releases", "text": "Abrir la página pública de releases y seguir futuras versiones.", "url": RELEASES_URL, "cta": "Abrir GitHub releases"}
            ]},
            {"type": "shot", "title": "Workspace actual", "text": "Revisa la interfaz renovada antes de descargar la aplicación.", "image": SCREEN_1, "caption_title": "Vista completa del workspace", "caption_text": "Proyecto, layout, modos de edición, escenario y salida estan mejor organizados."},
            {"type": "shot", "title": "Salida en vivo", "text": "La nueva vista previa ayuda a validar la composición con más rapidez.", "image": SCREEN_2, "caption_title": "Escena de salida", "caption_text": "Monitores oscuros y mejor espaciados hacen la lectura más inmediata."},
            {"type": "links", "title": "Recursos utiles", "text": "Continua con la guía de funcionamiento, los casos de uso o la FAQ.", "links": ["how-it-works", "use-cases", "faq", "compare"]}
        ],
    },
    "how-it-works": {
        "meta_title": f"Cómo funciona WallCraft Pro - refresh {PRODUCT_VERSION}",
        "meta_description": "Descubre cómo WallCraft Pro importa imágenes, las escala manualmente y previsualiza el resultado multi-monitor antes de aplicarlo.",
        "hero_badge": "Recorrido del workflow",
        "hero_title": "Cómo funciona el workflow renovado de WallCraft",
        "hero_lead": "La interfaz está construida alrededor de un ciclo más simple: importar, colocar, escalar, reordenar, previsualizar y aplicar.",
        "sections": [
            {"type": "steps", "title": "Cinco pasos desde las imágenes al escritorio", "text": "El workflow actual es más fácil de entender y controlar.", "steps": [
                {"title": "Importar imágenes", "text": "Cargar una o varias fotos en la biblioteca del proyecto."},
                {"title": "Construir la composición", "text": "Colocar las imágenes dentro del escritorio virtual y elegir un layout."},
                {"title": "Escalar sin distorsión", "text": "Usar el modo dedicado para cambiar el tamaño respetando la proporción."},
                {"title": "Ajustar el orden visual", "text": "Enviar una imagen atras o delante cuando hay superposiciones."},
                {"title": "Previsualizar y aplicar", "text": "Validar la vista multi-monitor y luego exportar o aplicar en Windows."}
            ]},
            {"type": "shot", "title": "Workspace actual", "text": "El nuevo layout mantiene las acciones importantes arriba y el escenario en el centro.", "image": SCREEN_1, "caption_title": "Workspace refresh", "caption_text": "Nuevo proyecto, modos de edición y biblioteca compacta mejoran el primer uso."},
            {"type": "shot", "title": "Escenario de composición", "text": "El escenario es más grande y más claro para editar.", "image": SCREEN_3, "caption_title": "Escenario y controles", "caption_text": "Escala, recorta y mueve imágenes directamente sobre el mapa virtual de monitores."}
        ],
    },
}

SITE_REFRESH_DE = {
    "home": {
        "meta_title": f"WallCraft Pro {PRODUCT_VERSION} - Multi-Monitor-Wallpaper-Generator für Windows 10/11",
        "meta_description": "WallCraft Pro 2026.3.14 bringt einen erneuerten Workspace, manuellen Skalierungsmodus, Ebenen-Reihenfolge und eine sauberere Ausgabevorschau.",
        "hero_badge": f"Produkt-Update {PRODUCT_VERSION}",
        "hero_title": "Wallpaper visuell für echte Multi-Monitor-Schreibtische gestalten",
        "hero_lead": "Das Update 2026.3.14 bringt einen klareren Workspace, manuelle proportionale Skalierung, Vor/Zurück für Ebenen und eine realistischere Ausgabevorschau.",
        "hero_points": [
            "Bilder in einem Workspace bewegen, skalieren, zuschneiden und neu anordnen.",
            "Das Ergebnis auf dunklen Monitorrahmen vor dem Anwenden prüfen.",
            "Das ganze Bild auf Dual-, Triple- und gemischten Setups sichtbar halten."
        ],
        "hero_caption_title": f"WallCraft {PRODUCT_VERSION} Workspace",
        "hero_caption_text": "Die erneuerte Oberfläche priorisiert Komposition, Schnellaktionen und visuelles Feedback.",
        "sections": [
            {"type": "cards", "title": f"Neu in {PRODUCT_VERSION}", "text": "Das Update konzentriert sich auf Ergonomie und visuelle Bearbeitung.", "cards": [
                {"title": "Erneuerter Workspace", "text": "Klarere Toolbar, größere Kompositionsfläche und kompaktere Bildbibliothek."},
                {"title": "Skalierungsmodus", "text": "Fotos vergrößern oder verkleinern, ohne das Seitenverhältnis zu verlieren."},
                {"title": "Ebenen-Reihenfolge", "text": "Bilder direkt aus der Bibliothek nach hinten oder vorne setzen."},
                {"title": "Neues Projekt", "text": "Mit einem Klick komplett neu starten."}
            ]},
            {"type": "shot", "title": "Moderner Workspace", "text": "Die aktuelle Version richtet die App stärker auf die Komposition aus.", "image": SCREEN_1, "caption_title": "Interface 2026.3.14", "caption_text": "Die neue Toolbar ordnet Sprache, Projekt, Layout, Bearbeitungsmodi und Anwendung logischer."},
            {"type": "shot", "title": "Saubere Ausgabevorschau", "text": "Die Vorschau wirkt ruhiger, klarer und näher an einem echten Desk-Setup.", "image": SCREEN_2, "caption_title": "Multi-Monitor-Vorschau", "caption_text": "Dunkle Monitore und mehr Abstand machen das Ergebnis leichter lesbar."}
        ],
    },
    "download": {
        "meta_title": f"WallCraft Pro für Windows 10/11 herunterladen - Update {PRODUCT_VERSION}",
        "meta_description": "Laden Sie WallCraft Pro für Windows 10/11 herunter und entdecken Sie das 2026.3.14-Update der Website und Benutzeroberfläche.",
        "hero_badge": f"Website- und UI-Refresh {PRODUCT_VERSION}",
        "hero_title": "WallCraft Pro für Windows 10/11 herunterladen",
        "hero_lead": "Die Website zeigt jetzt das Produkt-Update 2026.3.14. Die Windows-Datei bleibt über GitHub Releases verfügbar.",
        "sections": [
            {"type": "cards", "title": "Zugang wählen", "text": "Windows-Build laden, Quellcode öffnen oder GitHub Releases ansehen.", "cards": [
                {"title": "Aktueller Windows-Download", "text": "Die gepackte EXE über GitHub beziehen.", "url": DOWNLOAD_URL, "cta": f"v{PRODUCT_VERSION} herunterladen"},
                {"title": "Quellcode", "text": "Repository prüfen oder selbst bauen.", "url": REPO_URL, "cta": "Auf GitHub ansehen"},
                {"title": "GitHub Releases", "text": "Die öffentliche Release-Seite für Paket-Updates öffnen.", "url": RELEASES_URL, "cta": "GitHub Releases öffnen"}
            ]},
            {"type": "shot", "title": "Aktueller Workspace", "text": "Die erneuerte Oberfläche vor dem Download ansehen.", "image": SCREEN_1, "caption_title": "Vollstandiger Workspace", "caption_text": "Projekt, Layout, Bearbeitungsmodi, Kompositionsfläche und Ausgabe sind besser organisiert."},
            {"type": "shot", "title": "Live-Ausgabevorschau", "text": "Die neue Vorschau hilft dabei, die Komposition schneller zu validieren.", "image": SCREEN_2, "caption_title": "Ausgabe-Szene", "caption_text": "Dunkle Monitore und mehr Abstand verbessern die Lesbarkeit."}
        ],
    },
    "how-it-works": {
        "meta_title": f"So funktioniert WallCraft Pro - Refresh {PRODUCT_VERSION}",
        "meta_description": "Erfahren Sie, wie WallCraft Pro Bilder importiert, manuell skaliert und das Multi-Monitor-Ergebnis vor dem Anwenden anzeigt.",
        "hero_badge": "Workflow-Tour",
        "hero_title": "So funktioniert der erneuerte WallCraft-Workflow",
        "hero_lead": "Die Oberfläche basiert auf einem einfacheren Zyklus: importieren, platzieren, skalieren, ordnen, prüfen und anwenden.",
        "sections": [
            {"type": "steps", "title": "Funf Schritte vom Bild zum Desktop", "text": "Der aktuelle Workflow ist leichter zu verstehen und zu steuern.", "steps": [
                {"title": "Bilder importieren", "text": "Ein oder mehrere Fotos in die Projektbibliothek laden."},
                {"title": "Komposition aufbauen", "text": "Bilder im virtuellen Desktop platzieren und ein Layout wählen."},
                {"title": "Ohne Verzerrung skalieren", "text": "Den Skalierungsmodus nutzen, um die Größe mit festem Seitenverhältnis zu ändern."},
                {"title": "Ebenen-Reihenfolge anpassen", "text": "Bilder nach hinten oder vorne setzen, wenn Inhalte überlagern."},
                {"title": "Vorschau und Anwenden", "text": "Multi-Monitor-Vorschau prüfen und dann exportieren oder anwenden."}
            ]},
            {"type": "shot", "title": "Der aktuelle Workspace", "text": "Das neue Layout hält wichtige Aktionen oben und die Fläche in der Mitte.", "image": SCREEN_1, "caption_title": "Workspace-Refresh", "caption_text": "Neues Projekt, Bearbeitungsmodi und kompakte Bibliothek verbessern den Einstieg."},
            {"type": "shot", "title": "Kompositionsfläche im Detail", "text": "Die Fläche ist größer und klarer zu bearbeiten.", "image": SCREEN_3, "caption_title": "Fläche und Skalierungsgriffe", "caption_text": "Bilder direkt auf der virtuellen Monitor-Karte skalieren, zuschneiden und bewegen."}
        ],
    },
}

SITE_REFRESH = {
    "en": SITE_REFRESH_EN,
    "fr": SITE_REFRESH_FR,
    "es": SITE_REFRESH_ES,
    "de": SITE_REFRESH_DE,
}

for lang, updates in SITE_REFRESH.items():
    for page_key, page_updates in updates.items():
        PAGES[lang][page_key].update(page_updates)

# --- Version 2026.11 : taille réelle, Remplir, variantes stables, fond automatique ---
NOVEMBER_2026 = {
    "en": {
        "meta_description": f"WallCraft Pro {PRODUCT_VERSION} lines up one image across screens of different physical sizes, fills screens with face-aware cropping, keeps your wallpaper when you dock or undock, and rotates images automatically.",
        "hero_badge": f"New in {PRODUCT_VERSION}",
        "hero_lead": f"Version {PRODUCT_VERSION} aligns images on the real size of your screens, can fill every screen with face-aware cropping, and keeps your wallpaper in place when screens change.",
        "hero_points": [
            "Keep a horizon straight across a 27-inch and a 24-inch screen, gap between panels included.",
            "Choose Fit (whole images) or Fill (face-aware crop), then pick one of 4 stable variants.",
            "WallCraft stays in the notification area to reapply or rotate your wallpaper.",
        ],
        "whats_new": ("Four changes that matter on a real desk.", [
            ("Real screen size", "Screens are placed by their physical size, read from the display and adjustable, plus the gap between panels. Lines stay straight across screens of different sizes."),
            ("Fill with face-aware cropping", "The new Fill mode covers every screen. Each photo is cropped around detected faces, or around its most detailed area."),
            ("Stable layouts and variants", "Auto-Arrange gives the same result every time, and the Variants button shows four alternatives side by side."),
            ("Automatic wallpaper", "WallCraft remembers one wallpaper per screen setup, reapplies it after docking or a Windows theme reset, and can rotate images from a folder."),
        ]),
        "download_text": ("This version is about real desks rather than pixel grids.", [
            "The composition can follow the physical size of each screen instead of the Windows pixel grid.",
            "Fit keeps every image whole; Fill covers the screens and crops around faces.",
        ], [
            "Real screen size and gap between panels.",
            "Fill mode with face detection.",
            "Stable layouts and 4 variants to choose from.",
            "Notification-area icon, automatic reapply, rotation and start with Windows.",
        ], [
            "The Windows executable is built by GitHub Actions from the tagged source code and published on GitHub Releases with its SHA-256 checksum.",
            "WallCraft Pro is released under the MIT license.",
        ]),
    },
    "fr": {
        "meta_description": f"WallCraft Pro {PRODUCT_VERSION} aligne une image sur des écrans de tailles physiques différentes, remplit les écrans en recadrant autour des visages, garde le fond quand vous branchez un portable et fait tourner les images.",
        "hero_badge": f"Nouveau dans la {PRODUCT_VERSION}",
        "hero_lead": f"La version {PRODUCT_VERSION} aligne les images sur la taille réelle de vos écrans, peut remplir chaque écran en recadrant autour des visages et garde votre fond en place quand les écrans changent.",
        "hero_points": [
            "Une ligne d'horizon reste droite entre un 27 pouces et un 24 pouces, espace entre les dalles compris.",
            "Ajuster (images entières) ou Remplir (recadrage autour des visages), puis une variante parmi 4, toujours identiques.",
            "WallCraft reste dans la zone de notification pour réappliquer ou faire tourner le fond.",
        ],
        "whats_new": ("Quatre changements qui comptent sur un vrai bureau.", [
            ("Taille réelle des écrans", "Les écrans sont placés selon leur taille physique, lue dans l'écran et modifiable, et l'espace entre les dalles. Les lignes restent droites entre des écrans de tailles différentes."),
            ("Remplir autour des visages", "Le nouveau mode Remplir couvre chaque écran. Chaque photo est recadrée autour des visages détectés, sinon autour de sa zone la plus détaillée."),
            ("Dispositions stables et variantes", "Auto-Organiser donne toujours le même résultat, et le bouton Variantes montre quatre propositions côte à côte."),
            ("Fond automatique", "WallCraft mémorise un fond par configuration d'écrans, le réapplique après un branchement ou un retour du thème Windows, et peut faire tourner les images d'un dossier."),
        ]),
        "download_text": ("Cette version pense en vrais bureaux plutôt qu'en grilles de pixels.", [
            "La composition peut suivre la taille physique de chaque écran au lieu de la grille de pixels de Windows.",
            "Ajuster garde chaque image entière ; Remplir couvre les écrans et recadre autour des visages.",
        ], [
            "Taille réelle des écrans et espace entre les dalles.",
            "Mode Remplir avec détection des visages.",
            "Dispositions stables et 4 variantes au choix.",
            "Icône de notification, réapplication automatique, rotation et lancement au démarrage.",
        ], [
            "L'exécutable Windows est construit par GitHub Actions depuis le code source du tag et publié sur GitHub Releases avec son empreinte SHA-256.",
            "WallCraft Pro est distribué sous licence MIT.",
        ]),
    },
    "es": {
        "meta_description": f"WallCraft Pro {PRODUCT_VERSION} alinea una imagen entre pantallas de distinto tamaño físico, rellena las pantallas recortando alrededor de las caras, mantiene el fondo al conectar un portátil y rota imágenes automáticamente.",
        "hero_badge": f"Novedades de {PRODUCT_VERSION}",
        "hero_lead": f"La versión {PRODUCT_VERSION} alinea las imágenes según el tamaño real de sus pantallas, puede rellenar cada pantalla recortando alrededor de las caras y mantiene el fondo cuando cambian las pantallas.",
        "hero_points": [
            "Un horizonte sigue recto entre un monitor de 27 y otro de 24 pulgadas, con el espacio entre paneles.",
            "Ajustar (imágenes enteras) o Rellenar (recorte alrededor de las caras), y 4 variantes estables para elegir.",
            "WallCraft se queda en el área de notificación para volver a aplicar o rotar el fondo.",
        ],
        "whats_new": ("Cuatro cambios que importan en un escritorio real.", [
            ("Tamaño real de las pantallas", "Las pantallas se colocan según su tamaño físico, leído del monitor y modificable, y el espacio entre paneles. Las líneas siguen rectas entre pantallas de distinto tamaño."),
            ("Rellenar alrededor de las caras", "El nuevo modo Rellenar cubre cada pantalla. Cada foto se recorta alrededor de las caras detectadas o de su zona con más detalle."),
            ("Disposiciones estables y variantes", "Auto-Organizar da siempre el mismo resultado y el botón Variantes muestra cuatro alternativas lado a lado."),
            ("Fondo automático", "WallCraft guarda un fondo por configuración de pantallas, lo vuelve a aplicar tras conectar un portátil o si Windows restaura un tema, y puede rotar imágenes de una carpeta."),
        ]),
        "download_text": ("Esta versión piensa en escritorios reales y no en cuadrículas de píxeles.", [
            "La composición puede seguir el tamaño físico de cada pantalla en lugar de la cuadrícula de píxeles de Windows.",
            "Ajustar mantiene cada imagen entera; Rellenar cubre las pantallas y recorta alrededor de las caras.",
        ], [
            "Tamaño real de las pantallas y espacio entre paneles.",
            "Modo Rellenar con detección de caras.",
            "Disposiciones estables y 4 variantes para elegir.",
            "Icono de notificación, nueva aplicación automática, rotación e inicio con Windows.",
        ], [
            "GitHub Actions compila el ejecutable de Windows a partir del código fuente etiquetado y lo publica en GitHub Releases con su huella SHA-256.",
            "WallCraft Pro se distribuye bajo licencia MIT.",
        ]),
    },
    "de": {
        "meta_description": f"WallCraft Pro {PRODUCT_VERSION} richtet ein Bild über physisch unterschiedlich große Bildschirme aus, füllt Bildschirme mit gesichtsbasiertem Zuschnitt, behält das Hintergrundbild beim An- und Abdocken und wechselt Bilder automatisch.",
        "hero_badge": f"Neu in {PRODUCT_VERSION}",
        "hero_lead": f"Version {PRODUCT_VERSION} richtet Bilder an der realen Größe Ihrer Bildschirme aus, kann jeden Bildschirm mit gesichtsbasiertem Zuschnitt füllen und behält das Hintergrundbild, wenn sich die Bildschirme ändern.",
        "hero_points": [
            "Ein Horizont bleibt zwischen einem 27- und einem 24-Zoll-Monitor gerade, inklusive Abstand zwischen den Panels.",
            "Einpassen (ganze Bilder) oder Füllen (Zuschnitt um Gesichter), dann eine von 4 stabilen Varianten wählen.",
            "WallCraft bleibt im Infobereich, um das Hintergrundbild erneut anzuwenden oder zu wechseln.",
        ],
        "whats_new": ("Vier Änderungen, die an einem echten Schreibtisch zählen.", [
            ("Reale Bildschirmgröße", "Bildschirme werden nach ihrer physischen Größe platziert, aus dem Monitor gelesen und anpassbar, plus Abstand zwischen den Panels. Linien bleiben über unterschiedlich große Bildschirme gerade."),
            ("Füllen um Gesichter", "Der neue Modus Füllen bedeckt jeden Bildschirm. Jedes Foto wird um erkannte Gesichter zugeschnitten, sonst um seinen detailreichsten Bereich."),
            ("Stabile Layouts und Varianten", "Auto-Anordnen liefert immer dasselbe Ergebnis, und die Schaltfläche Varianten zeigt vier Alternativen nebeneinander."),
            ("Automatisches Hintergrundbild", "WallCraft merkt sich ein Hintergrundbild pro Bildschirmkonfiguration, wendet es nach dem Andocken oder einem Windows-Design-Reset erneut an und kann Bilder aus einem Ordner wechseln."),
        ]),
        "download_text": ("Diese Version denkt in echten Schreibtischen statt in Pixelrastern.", [
            "Die Komposition kann der physischen Größe jedes Bildschirms folgen statt dem Pixelraster von Windows.",
            "Einpassen zeigt jedes Bild vollständig; Füllen bedeckt die Bildschirme und schneidet um Gesichter zu.",
        ], [
            "Reale Bildschirmgröße und Abstand zwischen den Panels.",
            "Modus Füllen mit Gesichtserkennung.",
            "Stabile Layouts und 4 Varianten zur Auswahl.",
            "Symbol im Infobereich, automatisches erneutes Anwenden, Bildwechsel und Start mit Windows.",
        ], [
            "Die Windows-EXE wird von GitHub Actions aus dem getaggten Quellcode gebaut und mit ihrer SHA-256-Prüfsumme in GitHub Releases veröffentlicht.",
            "WallCraft Pro steht unter der MIT-Lizenz.",
        ]),
    },
}

_WHATS_NEW_TITLE = {"en": "What's new in {}", "fr": "Nouveautés de la {}", "es": "Novedades de {}", "de": "Neu in {}"}
_DOWNLOAD_TITLE = {"en": "What changed in {}", "fr": "Ce qui change dans la {}", "es": "Qué cambia en {}", "de": "Was sich in {} ändert"}
_ABOUT_DOWNLOAD = {"en": "About the download", "fr": "À propos du téléchargement", "es": "Sobre la descarga", "de": "Zum Download"}
_DOWNLOAD_LEAD = {
    "en": f"Download WallCraft Pro {PRODUCT_VERSION} for Windows 10/11. The executable is built from the public source code and published on GitHub Releases.",
    "fr": f"Téléchargez WallCraft Pro {PRODUCT_VERSION} pour Windows 10/11. L'exécutable est construit depuis le code source public et publié sur GitHub Releases.",
    "es": f"Descargue WallCraft Pro {PRODUCT_VERSION} para Windows 10/11. El ejecutable se compila desde el código fuente público y se publica en GitHub Releases.",
    "de": f"Laden Sie WallCraft Pro {PRODUCT_VERSION} für Windows 10/11 herunter. Die EXE wird aus dem öffentlichen Quellcode gebaut und in GitHub Releases veröffentlicht.",
}

for _lang, _n in NOVEMBER_2026.items():
    _home = PAGES[_lang]["home"]
    for _k in ("meta_description", "hero_badge", "hero_lead", "hero_points"):
        _home[_k] = _n[_k]
    _intro, _cards = _n["whats_new"]
    _home["sections"][0] = {"type": "cards", "title": _WHATS_NEW_TITLE[_lang].format(PRODUCT_VERSION), "text": _intro,
                            "cards": [{"title": t, "text": x} for t, x in _cards]}
    _dl = PAGES[_lang]["download"]
    _dl["meta_description"] = _n["meta_description"]
    _dl["hero_lead"] = _DOWNLOAD_LEAD[_lang]
    _intro, _body, _items, _aside = _n["download_text"]
    for _i, _section in enumerate(_dl["sections"]):
        if _section.get("type") == "text":
            _dl["sections"][_i] = {"type": "text", "title": _DOWNLOAD_TITLE[_lang].format(PRODUCT_VERSION), "text": _intro,
                                   "body": _body, "list": _items, "aside_title": _ABOUT_DOWNLOAD[_lang], "aside_body": _aside}
            break

# --- Interface 2026.11 : captures par langue, nouveautés, page d'aide (contenu : content_2026_11.py) ---
import content_2026_11 as _c


def screen(lang, name):
    """Capture de l'interface dans la langue de la page (site/assets/screens/<langue>/<nom>.webp)."""
    return f"assets/screens/{lang}/{name}.webp" if name != "desk" else "assets/screens/desk.webp"


def apply_2026_11():
    old_shots = {SCREEN_1: "main", SCREEN_2: "preview", SCREEN_3: "main-real-size"}
    for lang in LANG_ORDER:
        LANGS[lang]["nav"]["help"] = _c.NAV[lang]
        pages = PAGES[lang]
        # Plus aucune capture de l'ancienne interface
        for page in pages.values():
            for section in page.get("sections", []):
                if section.get("type") == "shot" and section.get("image") in old_shots:
                    section["image"] = screen(lang, old_shots[section["image"]])

        home = pages["home"]
        home["hero_image"] = screen(lang, "main")
        home["hero_caption_title"], home["hero_caption_text"] = _c.HERO_CAPTION[lang]
        intro, cards = _c.WHATS_NEW[lang]
        sections = [s for s in home["sections"] if s.get("type") not in ("shot", "steps")]
        sections[0] = {"type": "cards", "title": _WHATS_NEW_TITLE[lang].format(PRODUCT_VERSION), "text": intro,
                       "cards": [{"title": t, "text": x} for t, x in cards]}
        shots = [{"type": "shot", "title": t, "text": x, "image": screen(lang, img), "caption_title": ct, "caption_text": cx}
                 for t, x, img, ct, cx in _c.HOME_SHOTS[lang]]
        steps_intro, steps = _c.STEPS[lang]
        steps_section = {"type": "steps", "title": _c.HELP[lang]["sections"][0]["title"], "text": steps_intro,
                         "steps": [{"title": t, "text": x} for t, x in steps]}
        home["sections"] = [sections[0]] + shots + [steps_section] + sections[1:]
        for s in home["sections"]:
            if s.get("type") == "links" and "help" not in s["links"]:
                s["links"] = ["help"] + s["links"]

        for s in pages["download"]["sections"]:
            if s.get("type") == "text" and s.get("list"):
                s["list"] = [t + "." for t, _ in cards[:4]] + s["list"]
            if s.get("type") == "links" and "help" not in s["links"]:
                s["links"] = ["help"] + s["links"]

        how = pages["how-it-works"]
        how["sections"] = [steps_section] + [
            {"type": "feature", "title": h["title"], "text": h["text"], "image": screen(lang, h["image"]), "body": h["body"], "list": h["list"]}
            for h in _c.HELP[lang]["sections"] if h.get("type") == "feature" and h["image"] in ("main", "preview", "real-size")
        ] + [s for s in how["sections"] if s.get("type") == "links"]
        for s in how["sections"]:
            if s.get("type") == "links" and "help" not in s["links"]:
                s["links"] = ["help"] + s["links"]

        help_data = _c.HELP[lang]
        help_sections = []
        for h in help_data["sections"]:
            h = dict(h)
            if h["type"] == "steps":
                h["steps"] = [{"title": t, "text": x} for t, x in h["steps"]]
            if h["type"] == "feature":
                h["wide"] = h["image"] in ("main", "preview")
                h["image"] = screen(lang, h["image"])
            help_sections.append(h)
        toc = {"type": "toc", "title": _c.TOC[lang][0], "text": _c.TOC[lang][1],
               "links": [(h["id"], h["title"]) for h in help_sections if h.get("id")]}
        pages["help"] = {k: help_data[k] for k in ("meta_title", "meta_description", "hero_badge", "hero_title", "hero_lead")}
        pages["help"]["sections"] = [toc] + help_sections + [
            {"type": "links", "title": LANGS[lang]["related_title"], "text": "", "links": ["download", "how-it-works", "faq"]}]


apply_2026_11()


def page_label(lang, key):
    return LANGS[lang]["nav"][key]


def page_node(lang, key):
    slug = SLUGS[key]
    return posixpath.join(lang, slug) if slug else lang


def page_href(current_lang, current_key, target_lang, target_key):
    rel = posixpath.relpath(page_node(target_lang, target_key), start=page_node(current_lang, current_key))
    if rel == ".":
        return "index.html"
    return rel.rstrip("/") + "/index.html"


def render_action(lang, current_key, item, class_name="button secondary"):
    href = item.get("url") or page_href(lang, current_key, lang, item["page"])
    label = item.get("cta") or page_label(lang, item.get("page", "download"))
    attrs = ' target="_blank" rel="noopener noreferrer"' if item.get("url") else ""
    return f'<a class="{class_name}" href="{escape(href)}"{attrs}>{escape(label)}</a>'


def render_nav(lang, current_key):
    links = []
    for key in NAV_ORDER:
        href = page_href(lang, current_key, lang, key)
        active = " class=\"active\"" if key == current_key else ""
        links.append(f'<a{active} href="{href}">{escape(page_label(lang, key))}</a>')
    return "".join(links)


def render_lang_switch(lang, current_key):
    items = []
    for target in LANG_ORDER:
        href = page_href(lang, current_key, target, current_key)
        active = " class=\"active\"" if target == lang else ""
        items.append(f'<a{active} href="{href}" data-lang-link="{target}">{target.upper()}</a>')
    return "".join(items)


def render_card_grid(lang, current_key, cards):
    parts = []
    for card in cards:
        cta = ""
        if card.get("page") or card.get("url"):
            href = card.get("url") or page_href(lang, current_key, lang, card["page"])
            label = card.get("cta") or LANGS[lang]["read_page"]
            attrs = ' target="_blank" rel="noopener noreferrer"' if card.get("url") else ""
            cta = f'<p class="meta"><a class="card-link" href="{escape(href)}"{attrs}>{escape(label)}</a></p>'
        parts.append(f'<article class="card"><h3>{escape(card["title"])}</h3><p>{escape(card["text"])}</p>{cta}</article>')
    return '<div class="card-grid">' + "".join(parts) + '</div>'


def render_steps_grid(steps):
    cards = []
    for index, step in enumerate(steps, start=1):
        cards.append(f'<article class="card"><span class="mini-badge">{index:02d}</span><h3 style="margin-top:16px;">{escape(step["title"])}</h3><p>{escape(step["text"])}</p></article>')
    return '<div class="step-grid">' + "".join(cards) + '</div>'


def render_text_section(section):
    body = "".join(f"<p>{escape(item)}</p>" for item in section.get("body", []))
    listing = ""
    if section.get("list"):
        listing = '<ul class="feature-list">' + "".join(f"<li>{escape(item)}</li>" for item in section["list"]) + "</ul>"
    aside = ""
    if section.get("aside_title"):
        aside_body = "".join(f"<p>{escape(item)}</p>" for item in section.get("aside_body", []))
        aside = f'<aside class="note-box"><h3>{escape(section["aside_title"])}</h3>{aside_body}</aside>'
    return f'<div class="article-grid"><div class="panel prose">{body}{listing}</div>{aside}</div>'


def render_faq(section):
    items = []
    for question, answer in section["items"]:
        items.append(f'<details class="faq-item"><summary>{escape(question)}</summary><div class="answer"><p>{escape(answer)}</p></div></details>')
    return '<div class="faq-list">' + "".join(items) + '</div>'


def render_compare(section):
    head = "".join(f"<th>{escape(item)}</th>" for item in section["headers"])
    rows = []
    for row in section["rows"]:
        cells = "".join(f"<td>{escape(cell)}</td>" for cell in row)
        rows.append(f"<tr>{cells}</tr>")
    notes = ""
    if section.get("notes"):
        notes = '<div class="compare-summary">' + "".join(f'<article class="note-box"><h3>{escape(item["title"])}</h3><p>{escape(item["text"])}</p></article>' for item in section["notes"]) + '</div>'
    return f'<div class="compare-wrap"><table class="compare-table"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>{notes}'


def render_links(lang, current_key, section):
    cards = [{"title": page_label(lang, key), "text": PAGES[lang][key]["meta_description"], "page": key} for key in section["links"]]
    return render_card_grid(lang, current_key, cards)


SCREENSHOT_ALT = {
    "en": "WallCraft Pro interface screenshot",
    "fr": "Capture d'écran de l'interface WallCraft Pro",
    "es": "Captura de pantalla de la interfaz de WallCraft Pro",
    "de": "Screenshot der WallCraft-Pro-Oberfläche",
}

OG_LOCALES = {"en": "en_US", "fr": "fr_FR", "es": "es_ES", "de": "de_DE"}


def image_size(relative):
    """Taille réelle d'une image du site (pour éviter les sauts de mise en page), (640, 400) par défaut."""
    try:
        from PIL import Image
        with Image.open(ROOT / relative) as im:
            return im.size
    except Exception:
        return 640, 400


def render_feature(lang, prefix, section):
    body = "".join(f"<p>{escape(item)}</p>" for item in section.get("body", []))
    listing = '<ul class="feature-list">' + "".join(f"<li>{escape(i)}</li>" for i in section.get("list", [])) + "</ul>" if section.get("list") else ""
    w, h = image_size(section["image"])
    alt = escape(section["title"])
    wide = " wide" if section.get("wide") else ""
    return (f'<div class="feature-grid{wide}"><div class="panel prose">{body}{listing}</div>'
            f'<div class="feature-shot"><img src="{prefix}{escape(section["image"])}" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async"></div></div>')


def render_toc(section):
    return '<nav class="help-toc">' + "".join(f'<a href="#{escape(i)}">{escape(t)}</a>' for i, t in section["links"]) + "</nav>"


def render_shot(lang, prefix, section):
    alt = escape(section.get("caption_title") or SCREENSHOT_ALT[lang])
    w, h = image_size(section["image"])
    return f'''<div class="screen-card"><img src="{prefix}{escape(section["image"])}" alt="{alt}" width="{w}" height="{h}" loading="lazy" decoding="async"><div class="shot-caption"><strong>{escape(section["caption_title"])}</strong><p>{escape(section["caption_text"])}</p></div></div>'''


def render_section(lang, current_key, prefix, section):
    anchor = f' id="{escape(section["id"])}"' if section.get("id") else ""
    top = f'<section class="section"{anchor}><div class="section-head"><div><h2>{escape(section["title"])}</h2></div><p>{escape(section["text"])}</p></div>'
    if section["type"] == "cards":
        body = render_card_grid(lang, current_key, section["cards"])
    elif section["type"] == "steps":
        body = render_steps_grid(section["steps"])
    elif section["type"] == "text":
        body = render_text_section(section)
    elif section["type"] == "faq":
        body = render_faq(section)
    elif section["type"] == "compare":
        body = render_compare(section)
    elif section["type"] == "links":
        body = render_links(lang, current_key, section)
    elif section["type"] == "shot":
        body = render_shot(lang, prefix, section)
    elif section["type"] == "feature":
        body = render_feature(lang, prefix, section)
    elif section["type"] == "toc":
        body = render_toc(section)
    else:
        body = ""
    return top + body + "</section>"


def absolute_page_url(lang, key):
    url = f"{BASE_URL}{lang}/"
    if SLUGS[key]:
        url += f"{SLUGS[key]}/"
    return url


def default_cluster_url(key):
    return absolute_page_url("en", key)


def build_json_ld(lang, key):
    page = PAGES[lang][key]
    canonical_url = absolute_page_url(lang, key)
    website = {
        "@type": "WebSite",
        "name": "WallCraft Pro",
        "url": BASE_URL,
    }
    if key in {"home", "download", "how-it-works"}:
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "WallCraft Pro",
            "applicationCategory": "MultimediaApplication",
            "operatingSystem": "Windows 10, Windows 11",
            "softwareVersion": PRODUCT_VERSION,
            "url": canonical_url,
            "downloadUrl": DOWNLOAD_URL,
            "image": f"{BASE_URL}assets/screens/{lang}/main.webp",
            "inLanguage": lang,
            "description": page["meta_description"],
            "isAccessibleForFree": True,
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
            },
            "publisher": website,
        }
    return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": page["meta_title"],
        "url": canonical_url,
        "inLanguage": lang,
        "description": page["meta_description"],
        "isPartOf": website,
    }


def render_head(lang, current_key, prefix):
    page = PAGES[lang][current_key]
    hreflangs = []
    for l in LANG_ORDER:
        hreflangs.append(f'<link rel="alternate" hreflang="{l}" href="{absolute_page_url(l, current_key)}">')
    hreflangs.append(f'<link rel="alternate" hreflang="x-default" href="{default_cluster_url(current_key)}">')
    canonical_url = absolute_page_url(lang, current_key)
    verification_tag = f'\n    <meta name="google-site-verification" content="{escape(GOOGLE_SITE_VERIFICATION)}">' if GOOGLE_SITE_VERIFICATION else ""
    json_ld = json.dumps(build_json_ld(lang, current_key), ensure_ascii=False)
    
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(page["meta_title"])}</title>
    <meta name="description" content="{escape(page["meta_description"])}">
    <meta name="robots" content="index,follow,max-image-preview:large">
    <link rel="canonical" href="{canonical_url}">
    {" ".join(hreflangs)}
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="WallCraft Pro">
    <meta property="og:title" content="{escape(page["meta_title"])}">
    <meta property="og:description" content="{escape(page["meta_description"])}">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{BASE_URL}assets/screens/og-image.png">
    <meta property="og:locale" content="{OG_LOCALES[lang]}">
    <meta name="twitter:card" content="summary_large_image">
    {verification_tag}
    <script type="application/ld+json">{json_ld}</script>
    <link rel="stylesheet" href="{prefix}site.css">
</head>
<body>
'''


def render_footer(lang, current_key, prefix):
    about_title = LANGS[lang]["footer_about_title"]
    about_text = LANGS[lang]["footer_about_text"]
    resources_title = LANGS[lang]["footer_resources_title"]
    source_title = LANGS[lang]["footer_source_title"]
    source_text = LANGS[lang]["footer_source_text"]
    
    resource_links = []
    for key in FOOTER_ORDER:
        href = page_href(lang, current_key, lang, key)
        resource_links.append(f'<li><a href="{href}">{escape(page_label(lang, key))}</a></li>')
        
    return f'''
    <footer class="footer">
        <div class="footer-grid">
            <div class="footer-col">
                <h3>{about_title}</h3>
                <p>{about_text}</p>
                <div class="lang-selector">{render_lang_switch(lang, current_key)}</div>
            </div>
            <div class="footer-col">
                <h3>{resources_title}</h3>
                <ul class="footer-links">{"".join(resource_links)}</ul>
            </div>
            <div class="footer-col">
                <h3>{source_title}</h3>
                <p>{source_text}</p>
                <div style="margin-top: 16px;">
                    <a class="button secondary small" href="{REPO_URL}" target="_blank" rel="noopener noreferrer">{LANGS[lang]["view_source"]}</a>
                    <a class="button secondary small" style="margin-left: 10px;" href="{ARCHI_IT_HOME_URL}" target="_blank" rel="noopener noreferrer">Archi-IT</a>
                    <a class="button secondary small" style="margin-left: 10px;" href="{ARCHI_IT_URL}" target="_blank" rel="noopener noreferrer">{escape(LANGS[lang]["footer_hub_label"])}</a>
                </div>
            </div>
        </div>
        <div class="footer-bottom">
            <p>&copy; {TODAY[:4]} WallCraft Pro. {LANGS[lang]["updated"]} {TODAY}.</p>
        </div>
    </footer>
    <script src="{prefix}site.js"></script>
</body>
</html>
'''

def render_page(lang, key):
    page = PAGES[lang][key]
    prefix = rel_prefix(key)
    
    sections_html = []
    for section in page.get("sections", []):
        sections_html.append(render_section(lang, key, prefix, section))
        
    hero_badge = f'<span class="mini-badge">{escape(page["hero_badge"])}</span>' if page.get("hero_badge") else ""
    hero_points = "".join(f'<li>{escape(p)}</li>' for p in page.get("hero_points", []))
    hero_points_html = f'<ul class="feature-list hero-list">{hero_points}</ul>' if hero_points else ""
    
    hero_caption = ""
    if page.get("hero_caption_title"):
        hero_caption = f'<div class="shot-caption"><strong>{escape(page["hero_caption_title"])}</strong><p>{escape(page["hero_caption_text"])}</p></div>'

    hero_image = ""
    if key == "home":
        hero_src = page.get("hero_image", SCREEN_1)
        hw, hh = image_size(hero_src)
        hero_image = f'''<div class="hero-image">
            <div class="screen-card">
                <img src="{prefix}{hero_src}" alt="{escape(SCREENSHOT_ALT[lang])}" width="{hw}" height="{hh}">
                {hero_caption}
            </div>
        </div>'''

    content = f'''
    <header class="topbar">
        <div class="topbar-inner">
            <a href="{page_href(lang, key, lang, "home")}" class="logo">WallCraft <span>Pro</span></a>
            <nav class="nav">{render_nav(lang, key)}</nav>
            <div class="nav-actions">
                <a class="button secondary small" href="https://ko-fi.com/D1D21VSKW5" target="_blank" rel="noopener noreferrer">{LANGS[lang]["support"]}</a>
                <a class="button small" href="{DOWNLOAD_URL}">{LANGS[lang]["nav"]["download"]}</a>
            </div>
        </div>
    </header>

    <main id="content">
        <header class="hero{"" if hero_image else " no-image"}">
            <div class="hero-head">
                {hero_badge}
                <h1>{escape(page["hero_title"])}</h1>
            </div>
            <div class="hero-content">
                <p class="lead">{escape(page["hero_lead"])}</p>
                {hero_points_html}
                <div class="hero-actions">
                    <a class="button" href="{DOWNLOAD_URL}">{LANGS[lang]["download_now"]}</a>
                    <a class="button secondary" href="{page_href(lang, key, lang, "how-it-works")}">{LANGS[lang]["learn_more"]}</a>
                </div>
            </div>
            {hero_image}
        </header>

        {"".join(sections_html)}

        <section class="section ready-section">
            <div class="panel highlight-panel">
                <h2>{escape(LANGS[lang]["ready_title"])}</h2>
                <p>{escape(LANGS[lang]["ready_text"])}</p>
                <div class="hero-actions" style="margin-top: 24px;">
                    <a class="button" href="{DOWNLOAD_URL}">{LANGS[lang]["download_now"]}</a>
                    <a class="button secondary" href="https://ko-fi.com/D1D21VSKW5" target="_blank" rel="noopener noreferrer">{LANGS[lang]["support"]}</a>
                </div>
            </div>
        </section>
    </main>
    '''
    
    return render_head(lang, key, prefix) + content + render_footer(lang, key, prefix)


def build_site():
    if HTML_ROOT.exists():
        shutil.rmtree(HTML_ROOT)
    HTML_ROOT.mkdir(parents=True, exist_ok=True)
    
    # Copy assets
    asset_src = ROOT / "assets"
    if asset_src.exists():
        shutil.copytree(asset_src, HTML_ROOT / "assets")
        
    # Build pages
    for lang in LANG_ORDER:
        for key in PAGES[lang]:
            out_dir = page_dir(lang, key)
            out_dir.mkdir(parents=True, exist_ok=True)
            html = render_page(lang, key)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            
    # Write CSS and JS files
    (HTML_ROOT / "site.css").write_text(CSS_CONTENT, encoding="utf-8")
    (HTML_ROOT / "site.js").write_text(JS_CONTENT, encoding="utf-8")
    
    print(f"Site built successfully in {HTML_ROOT}")


def build_sitemap_xml():
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    for key in PAGES["en"]:
        for lang in LANG_ORDER:
            lines.append("  <url>")
            lines.append(f"    <loc>{absolute_page_url(lang, key)}</loc>")
            lines.append(f"    <lastmod>{TODAY}</lastmod>")
            for alt_lang in LANG_ORDER:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{alt_lang}" href="{absolute_page_url(alt_lang, key)}" />')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{default_cluster_url(key)}" />')
            lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_robots_txt():
    return f"""User-agent: *
Allow: /

Sitemap: {PROJECT_BASE_URL}sitemap.xml
"""


def build_search_console_guide():
    return f"""# Google Search Console Setup

## Recommended property
- Preferred URL-prefix property: `{PROJECT_BASE_URL}`
- Main multilingual site URL: `{BASE_URL}`
- Sitemap to submit: `{PROJECT_BASE_URL}sitemap.xml`

## What is included
- `sitemap.xml` with all FR / EN / ES / DE pages
- `hreflang` alternates on every generated page
- `canonical` tags on every generated page
- `robots.txt`
- JSON-LD metadata for Google-rich understanding

## Verification
If Google gives you a meta-tag token, put it in `GOOGLE_SITE_VERIFICATION` inside `site_builder.py`, then rebuild the site.

## Hosting note
This project is designed for a GitHub Pages project site under a subpath. The sitemap is the most important file to submit manually in Search Console.
If you later move to a custom domain, keep the same sitemap URL pattern and place `robots.txt` at the domain root.
"""

def build_router():
    html_router = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WallCraft Pro language router</title>
    <meta name="robots" content="noindex,follow">
    <script>
        (function () {
            const supported = ["fr", "en", "es", "de"];
            const params = new URLSearchParams(window.location.search);
            const saved = window.localStorage.getItem("wallcraft.lang");
            const candidates = [params.get("lang"), saved].concat(navigator.languages || [navigator.language || ""]);
            for (const value of candidates) {
                if (!value) continue;
                const normalized = String(value).toLowerCase().split("-")[0];
                if (supported.includes(normalized)) {
                    window.location.replace("./" + normalized + "/index.html");
                    return;
                }
            }
            window.location.replace("./en/index.html");
        })();
    </script>
</head>
<body>
    <p>Select a language:</p>
    <ul>
        <li><a href="./fr/index.html">Français</a></li>
        <li><a href="./en/index.html">English</a></li>
        <li><a href="./es/index.html">Español</a></li>
        <li><a href="./de/index.html">Deutsch</a></li>
    </ul>
</body>
</html>'''
    (HTML_ROOT / "index.html").write_text(html_router, encoding="utf-8")


def build_google_package():
    sitemap = build_sitemap_xml()
    robots = build_robots_txt()
    guide = build_search_console_guide()

    (HTML_ROOT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (HTML_ROOT / "robots.txt").write_text(robots, encoding="utf-8")
    (ROOT / "GOOGLE_SEARCH_CONSOLE_SETUP.md").write_text(guide, encoding="utf-8")

if __name__ == "__main__":
    build_site()
    build_router()
    build_google_package()
