import locale
import ctypes

# Current application language
_CURRENT_LANG = "en"

# Available languages
LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch"
}

# Translation Dictionary
_STRINGS = {
    "app_title": {
        "en": "WallCraft",
        "fr": "WallCraft",
        "es": "WallCraft",
        "de": "WallCraft"
    },
    "monitors_count": {
        "en": "{} screen(s)",
        "fr": "{} écran(s)",
        "es": "{} pantalla(s)",
        "de": "{} Bildschirm(e)"
    },
    "btn_add_images": {
        "en": "+ Add Images",
        "fr": "+ Ajouter des Images",
        "es": "+ Añadir Imágenes",
        "de": "+ Bilder hinzufügen"
    },
    "lbl_layout": {
        "en": "Layout:",
        "fr": "Disposition:",
        "es": "Disposición:",
        "de": "Anordnung:"
    },
    "layout_mosaic": {
        "en": "Perfect Mosaic",
        "fr": "Mosaïque Parfaite",
        "es": "Mosaico Perfecto",
        "de": "Perfektes Mosaik"
    },
    "layout_lines": {
        "en": "Justified Lines",
        "fr": "Lignes Justifiées",
        "es": "Líneas Justificadas",
        "de": "Ausgerichtete Linien"
    },
    "layout_grid": {
        "en": "Regular Grid",
        "fr": "Grille Régulière",
        "es": "Cuadrícula Regular",
        "de": "Regelmäßiges Raster"
    },
    "layout_v_strip": {
        "en": "Vertical Strips",
        "fr": "Bandes Verticales",
        "es": "Bandas Verticales",
        "de": "Vertikale Streifen"
    },
    "layout_h_strip": {
        "en": "Horizontal Strips",
        "fr": "Bandes Horizontales",
        "es": "Bandas Horizontales",
        "de": "Horizontale Streifen"
    },
    "layout_optimal": {
        "en": "Maximum Optimization (Slow)",
        "fr": "Optimisation Maximale (Lent)",
        "es": "Optimización Máxima (Lento)",
        "de": "Maximale Optimierung (Langsam)"
    },
    "btn_auto_arrange": {
        "en": "🎲 Auto-Arrange",
        "fr": "🎲 Auto-Organiser",
        "es": "🎲 Auto-Organizar",
        "de": "🎲 Auto-Anordnen"
    },
    "btn_mode_move": {
        "en": "Mode: MOVE",
        "fr": "Mode: DÉPLACER",
        "es": "Modo: MOVER",
        "de": "Modus: BEWEGEN"
    },
    "btn_mode_crop": {
        "en": "Mode: CROP",
        "fr": "Mode: ROGNER",
        "es": "Modo: RECORTAR",
        "de": "Modus: ZUSCHNEIDEN"
    },
    "btn_remove": {
        "en": "🗑️ Remove Image",
        "fr": "🗑️ Supprimer l'image",
        "es": "🗑️ Eliminar imagen",
        "de": "🗑️ Bild entfernen"
    },
    "chk_show_monitors": {
        "en": "View Monitors",
        "fr": "Voir Ecrans",
        "es": "Ver Monitores",
        "de": "Monitore anzeigen"
    },
    "btn_apply": {
        "en": "🖥️ Apply Wallpaper",
        "fr": "🖥️ Appliquer en Fond",
        "es": "🖥️ Fondo de Pantalla",
        "de": "🖥️ Hintergrundbild"
    },
    "status_ready": {
        "en": "Ready",
        "fr": "Prêt",
        "es": "Listo",
        "de": "Bereit"
    },
    "status_processing": {
        "en": "Processing...",
        "fr": "Traitement...",
        "es": "Procesando...",
        "de": "Wird bearbeitet..."
    },
    "err_no_monitors": {
        "en": "No monitors detected",
        "fr": "Aucun écran détecté",
        "es": "No se detectaron monitores",
        "de": "Keine Monitore erkannt"
    },
    "msg_apply_ok": {
        "en": "Wallpaper successfully applied to specific screens!",
        "fr": "Wallpaper appliqué par écran !",
        "es": "¡Fondo de pantalla aplicado a pantallas específicas!",
        "de": "Hintergrundbild erfolgreich angewendet!"
    },
    "err_api_fail": {
        "en": "Windows API failed. The wallpaper might not be applied correctly.",
        "fr": "Echec API Windows. Le fond n'a peut-être pas été appliqué.",
        "es": "Fallo de la API de Windows. Puede que el fondo no se aplicara.",
        "de": "Windows API fehlgeschlagen."
    },
    "msg_optimal_warn_title": {
        "en": "Optimization Engine",
        "fr": "Heuristique",
        "es": "Heurística",
        "de": "Heuristik"
    },
    "msg_optimal_warn_text": {
        "en": "Finding the mathematical perfect packing (Slicing Floorplan) may take up to 1 second depending on the image count. Please wait while the algorithm simulates all combinations...",
        "fr": "La recherche d'imbrication parfaite (Slicing Floorplan) peut prendre jusqu'à 1 seconde selon le nombre d'images. Merci de patienter pendant que l'algorithme teste toutes les dimensions...",
        "es": "Encontrar el empaquetado matemático perfecto puede tardar hasta 1 segundo. Por favor, espere...",
        "de": "Die Suche nach der perfekten mathematischen Anordnung kann bis zu 1 Sekunde dauern. Bitte haben Sie Geduld..."
    },
    "lang_select": {
        "en": "Language/Langue:",
        "fr": "Langue/Language:",
        "es": "Idioma/Lang:",
        "de": "Sprache/Lang:"
    }
}

def detect_os_language():
    """Detect default OS language, fallback to English."""
    try:
        windll = ctypes.windll.kernel32
        lang_id = windll.GetUserDefaultUILanguage()
        primary_lang_id = lang_id & 0x3ff
        # 0x09: English, 0x0C: French, 0x0A: Spanish, 0x07: German
        if primary_lang_id == 0x0C: return "fr"
        if primary_lang_id == 0x0A: return "es"
        if primary_lang_id == 0x07: return "de"
    except Exception:
        pass
    return "en"

def set_language(lang_code):
    """Sets the current application language."""
    global _CURRENT_LANG
    if lang_code in LANGUAGES:
        _CURRENT_LANG = lang_code
    return _CURRENT_LANG

def get_current_language():
    return _CURRENT_LANG

def tr(key, *args):
    """Translate a given key into the current language, with formatting."""
    lang_dict = _STRINGS.get(key)
    if not lang_dict:
        return key # fallback to returning the key if missing
    
    text = lang_dict.get(_CURRENT_LANG, lang_dict.get("en", key))
    if args:
        return text.format(*args)
    return text

# Initialization
set_language(detect_os_language())
