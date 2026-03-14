from pathlib import Path
import json
import posixpath
import shutil
from html import escape

TODAY = "2026-03-13"
BASE_URL = "https://rangornrar.github.io/MultiScreenWallpaper/html/"
REPO_URL = "https://github.com/rangornrar/MultiScreenWallpaper"
DOWNLOAD_URL = "https://github.com/rangornrar/MultiScreenWallpaper/releases/download/v1.0/WallCraft-Pro-v1.0.0-Windows.exe"
RELEASES_URL = f"{REPO_URL}/releases"
SCREEN_1 = "assets/wallcraft_app_ui_1773221294829.png"
SCREEN_2 = "assets/wallcraft_optimal_layout_1773221310533.png"

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
.logo { font-size: 1.4em; font-weight: 800; color: #fff; }
.logo span { color: var(--accent); }
.nav { display: flex; gap: 24px; }
.nav a { color: var(--text-dim); font-size: 0.95em; }
.nav a:hover, .nav a.active { color: var(--accent); }

.hero {
    padding: 80px 20px;
    max-width: 1100px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 60px;
    align-items: center;
}
.hero-content h1 { font-size: 3.5em; line-height: 1.1; margin-bottom: 24px; color: #fff; font-weight: 800; }
.hero-content .lead { font-size: 1.25em; color: var(--text-dim); margin-bottom: 32px; }
.hero-actions { display: flex; gap: 16px; flex-wrap: wrap; }

.section { padding: 80px 20px; max-width: 1100px; margin: 0 auto; }
.section-head { margin-bottom: 48px; max-width: 700px; }
.section-head h2 { font-size: 2.2em; color: #fff; margin-bottom: 16px; }
.section-head p { font-size: 1.1em; color: var(--text-dim); }

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
.card h3 { color: #fff; margin-bottom: 12px; font-size: 1.4em; }
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
.highlight-panel h2 { font-size: 2.5em; color: #fff; margin-bottom: 24px; }

@media (max-width: 900px) {
    .hero { grid-template-columns: 1fr; text-align: center; padding: 40px 20px; }
    .hero-content h1 { font-size: 2.5em; }
    .hero-actions { justify-content: center; }
    .footer-grid { grid-template-columns: 1fr; gap: 40px; }
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
}

NAV_ORDER = ["download", "how-it-works", "dual-monitor-wallpaper-windows-11", "use-cases", "faq", "compare"]
FOOTER_ORDER = ["download", "how-it-works", "faq", "compare", "dual-monitor-wallpaper-without-cropping", "mixed-monitor-wallpaper-setup"]
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
        "footer_about_text": "Open-source Windows app for building, splitting, and applying wallpapers across uneven monitor setups without cropping or distortion.",
        "footer_resources_title": "Pages",
        "footer_source_title": "Project",
        "footer_source_text": "The source code is public on GitHub, and the first packaged release is now available through GitHub Releases as v1.0.0 for Windows.",
        "download_now": "Download v1.0.0 for Windows",
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
        "footer_about_text": "Application Windows open source pour créer, découper et appliquer des fonds d'écran sur des configurations multi-écrans irrégulières, sans rognage ni déformation.",
        "footer_resources_title": "Pages",
        "footer_source_title": "Projet",
        "footer_source_text": "Le code source est public sur GitHub, et la première release packagée est maintenant disponible via GitHub Releases en version v1.0.0 pour Windows.",
        "download_now": "Télécharger v1.0.0 pour Windows",
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
            "how-it-works": "Como funciona",
            "dual-monitor-wallpaper-windows-11": "Doble monitor",
            "faq": "FAQ",
            "compare": "Comparar",
            "use-cases": "Casos de uso",
            "dual-monitor-wallpaper-without-cropping": "Guia sin recortes",
            "mixed-monitor-wallpaper-setup": "Monitores mixtos",
        },
        "footer_about_title": "WallCraft Pro",
        "footer_about_text": "Aplicacion open source para Windows que crea, divide y aplica fondos en configuraciones con monitores desiguales, sin recortar ni deformar las imagenes.",
        "footer_resources_title": "Paginas",
        "footer_source_title": "Proyecto",
        "footer_source_text": "El codigo fuente es publico en GitHub y la primera release empaquetada ya esta disponible en GitHub Releases como v1.0.0 para Windows.",
        "download_now": "Descargar v1.0.0 para Windows",
        "view_source": "Ver en GitHub",
        "view_releases": "Abrir releases de GitHub",
        "learn_more": "Ver como funciona",
        "related_title": "Seguir explorando",
        "ready_title": "Listo para crear un fondo que de verdad encaje con tu escritorio?",
        "ready_text": "Descarga la build actual, prueba tu disposicion de monitores y deja el repositorio de GitHub a mano para actualizaciones y codigo fuente.",
        "read_page": "Leer pagina",
        "updated": "Actualizado",
    },
    "de": {
        "name": "Deutsch",
        "locale": "de_DE",
        "tagline": "Open-Source-Studio fur Multi-Monitor-Wallpaper",
        "skip": "Zum Inhalt springen",
        "support": "Mich auf Ko-fi unterstutzen",
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
        "footer_about_text": "Open-Source-Windows-App zum Erstellen, Aufteilen und Anwenden von Wallpapern fur ungleichmassige Multi-Monitor-Setups, ohne Zuschnitt oder Verzerrung.",
        "footer_resources_title": "Seiten",
        "footer_source_title": "Projekt",
        "footer_source_text": "Der Quellcode ist auf GitHub offentlich, und die erste paketierte Release ist jetzt uber GitHub Releases als v1.0.0 fur Windows verfugbar.",
        "download_now": "v1.0.0 fur Windows herunterladen",
        "view_source": "Auf GitHub ansehen",
        "view_releases": "GitHub-Releases offnen",
        "learn_more": "So funktioniert es",
        "related_title": "Weiterlesen",
        "ready_title": "Bereit fur ein Wallpaper, das wirklich zu deinem Setup passt?",
        "ready_text": "Lade den aktuellen Build herunter, teste dein Multi-Monitor-Layout und nutze das GitHub-Repository fur Updates und Quellcode.",
        "read_page": "Seite lesen",
        "updated": "Aktualisiert",
    },
}

FAQ_ITEMS = {
    "en": [
        ("Does WallCraft Pro crop images?", "No. The tool is designed around a fit-inside rule so the original image stays visible. Empty space can still exist, but cropping and distortion are avoided."),
        ("Does it work with different monitor sizes?", "Yes. Mixed resolutions, different heights, and uneven desk layouts are the core use case."),
        ("Can I export and split by screen?", "Yes. The app can export a large composition and split the result into per-monitor images mapped to your physical setup."),
        ("Can it apply wallpapers directly on Windows?", "Yes. The project uses the native Windows desktop wallpaper API when available, with a span fallback when needed."),
        ("Is it open source?", "Yes. The source code is public on GitHub, which helps with trust, inspection, and community contributions."),
        ("Is there a versioned GitHub release already?", "Yes. The first public packaged release is now available as v1.0.0 on GitHub Releases, with a dedicated Windows executable."),
    ],
    "fr": [
        ("WallCraft Pro rogne-t-il les images ?", "Non. L'outil suit une logique fit-inside: l'image originale reste visible. Il peut rester des marges, mais le rognage et la déformation sont évités."),
        ("Est-ce que cela fonctionne avec des écrans de tailles différentes ?", "Oui. Les résolutions mixtes, les hauteurs différentes et les dispositions irrégulières sont précisément le cas d'usage visé."),
        ("Peut-on exporter et découper par écran ?", "Oui. L'application peut exporter une grande composition puis la découper en images par moniteur selon ta disposition physique."),
        ("Peut-elle appliquer le fond d'écran directement sur Windows ?", "Oui. Le projet utilise l'API native de fond d'écran Windows quand elle est disponible, avec un mode panorama en secours."),
        ("Le projet est-il open source ?", "Oui. Le code source est public sur GitHub, ce qui aide pour la confiance, l'inspection et les contributions."),
        ("Y a-t-il déjà une vraie GitHub Release versionnée ?", "Oui. La première release publique packagée est maintenant disponible en v1.0.0 sur GitHub Releases, avec un exécutable Windows dédié."),
    ],
    "es": [
        ("WallCraft Pro recorta las imagenes?", "No. La herramienta sigue una logica fit-inside para mantener visible la imagen original. Puede quedar espacio vacio, pero evita recortes y deformacion."),
        ("Funciona con monitores de distintos tamanos?", "Si. Resoluciones mixtas, alturas distintas y disposiciones irregulares son justo el caso de uso principal."),
        ("Puedo exportar y dividir por pantalla?", "Si. La aplicacion puede exportar una composicion grande y dividir el resultado en imagenes por monitor."),
        ("Puede aplicar el fondo directamente en Windows?", "Si. El proyecto usa la API nativa de fondos de Windows cuando esta disponible, con modo panoramico como respaldo."),
        ("Es open source?", "Si. El codigo fuente es publico en GitHub, lo que mejora la confianza, la revision y las contribuciones."),
        ("Ya existe una release versionada en GitHub?", "Si. La primera release publica empaquetada ya esta disponible como v1.0.0 en GitHub Releases, con un ejecutable dedicado para Windows."),
    ],
    "de": [
        ("Schneidet WallCraft Pro Bilder zu?", "Nein. Das Tool arbeitet nach einem Fit-Inside-Prinzip, damit das Originalbild sichtbar bleibt. Leerraum ist moglich, Zuschnitt und Verzerrung aber nicht."),
        ("Funktioniert es mit unterschiedlich grossen Monitoren?", "Ja. Gemischte Auflosungen, verschiedene Hohen und ungleichmassige Setups sind genau der Kern-Anwendungsfall."),
        ("Kann ich nach Monitor exportieren und aufteilen?", "Ja. Die App kann eine grosse Komposition exportieren und das Ergebnis passend zu deinem physischen Setup in Einzelbilder pro Monitor teilen."),
        ("Kann die App Wallpaper direkt unter Windows anwenden?", "Ja. Das Projekt nutzt die native Windows-Desktop-Wallpaper-API, wenn sie verfugbar ist, und wechselt sonst auf einen Span-Fallback."),
        ("Ist das Projekt Open Source?", "Ja. Der Quellcode ist auf GitHub offentlich, was Vertrauen, Prufbarkeit und Beitrage erleichtert."),
        ("Gibt es schon eine versionierte GitHub-Release?", "Ja. Die erste offentliche paketierte Release ist jetzt als v1.0.0 in GitHub Releases verfugbar, mit einer eigenen Windows-EXE."),
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
                    {"title": "Official Windows release", "text": "Download the packaged executable for Windows 10/11.", "url": DOWNLOAD_URL, "cta": "Download v1.0.0 for Windows"},
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
                    {"title": "Release oficial para Windows", "text": "Descargar el ejecutable para Windows 10/11.", "url": DOWNLOAD_URL, "cta": "Descargar v1.0.0 para Windows"},
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
                    {"title": "Offizielle Windows-Release", "text": "Download der EXE für Windows 10/11.", "url": DOWNLOAD_URL, "cta": "v1.0.0 herunterladen"},
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
                    ["WallCraft Pro", "Statische Wallpaper auf Mix-Desks", "Kein Zuschnitt, Aufteilung, nativ", "Erhalt des ganzen Bildes"],
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
                    {"title": "Release Windows officielle", "text": "Télécharger l'exécutable packagé pour Windows 10/11.", "url": DOWNLOAD_URL, "cta": "Télécharger v1.0.0 pour Windows"},
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
                {"type": "text", "title": "Le problème du double écran hétérogène", "text": "Deux écrans ne partagent quasiment jamais un rectangle parfait.", "body": ["Un écran peut être plus haut, décalé ou vertical.", "C'est pour cela que les réglages 'Remplir' ou 'Étendre' sont souvent frustrants."], "list": ["Hauteurs différentes.", "Ratios différents.", "Sujet coupé par les bordures."], "aside_title": "L'approche WallCraft", "aside_body": ["WallCraft conserve l'image entière au lieu de forcer un crop destructif.", "Il s'adapte à la géométrie réelle de votre bureau."]},
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
                    ["DisplayFusion", "Gestion globale du bureau multi-écrans", "Fenêtres, outils moniteurs et productivité", "Plus complexe pour la simple composition de fonds"]
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
            "hero_lead": "Découvrez comment WallCraft Pro s'adapte à diverses configurations.",
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
                {"type": "text", "title": "Le défi de la géométrie", "text": "Un écran plus haut ou vertical change tout.", "body": ["Une bonne configuration assume que les moniteurs ne forment pas un rectangle parfait.", "Le workflow s'adapte à cette géométrie au lieu de forcer un crop global."], "list": ["Résolutions différentes.", "Hauteurs physiques différentes.", "Ratios différents."], "aside_title": "Ce que WallCraft apporte", "aside_body": ["Il traite la carte des écrans comme un élément central du workflow.", "Vos fonds d'écran paraissent être créés sur mesure pour votre bureau."]},
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


def render_shot(prefix, section):
    return f'''<div class="screen-card"><img src="{prefix}{escape(section["image"])}" alt="WallCraft screenshot" width="640" height="640" loading="lazy" decoding="async"><div class="shot-caption"><strong>{escape(section["caption_title"])}</strong><p>{escape(section["caption_text"])}</p></div></div>'''


def render_section(lang, current_key, prefix, section):
    top = f'<section class="section"><div class="section-head"><div><h2>{escape(section["title"])}</h2></div><p>{escape(section["text"])}</p></div>'
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
        body = render_shot(prefix, section)
    else:
        body = ""
    return top + body + "</section>"


def render_head(lang, current_key, prefix):
    page = PAGES[lang][current_key]
    hreflangs = []
    for l in LANG_ORDER:
        url = f"{BASE_URL}{l}/"
        if SLUGS[current_key]:
            url += f"{SLUGS[current_key]}/"
        hreflangs.append(f'<link rel="alternate" hreflang="{l}" href="{url}">')
    
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(page["meta_title"])}</title>
    <meta name="description" content="{escape(page["meta_description"])}">
    {" ".join(hreflangs)}
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
        hero_image = f'''<div class="hero-image">
            <div class="screen-card">
                <img src="{prefix}{SCREEN_1}" alt="App screenshot" width="600" height="400">
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
        <header class="hero">
            <div class="hero-content">
                {hero_badge}
                <h1>{escape(page["hero_title"])}</h1>
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

def build_router():
    # Simple lang router for the root index.html
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=./fr/index.html">
    <script>window.location.href = "./fr/index.html";</script>
</head>
<body>
    <p>Redirecting to <a href="./fr/index.html">French version</a> / <a href="./en/index.html">English version</a></p>
</body>
</html>'''
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    (HTML_ROOT / "index.html").write_text(html, encoding="utf-8")

if __name__ == "__main__":
    build_site()
    build_router()
