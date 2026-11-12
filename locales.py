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
        "en": "Add images",
        "fr": "Ajouter des images",
        "es": "Añadir imágenes",
        "de": "Bilder hinzufügen"
    },
    "lbl_layout": {
        "en": "Layout",
        "fr": "Disposition",
        "es": "Disposición",
        "de": "Anordnung"
    },
    "layout_mosaic": {
        "en": "Perfect mosaic",
        "fr": "Mosaïque parfaite",
        "es": "Mosaico perfecto",
        "de": "Perfektes Mosaik"
    },
    "layout_lines": {
        "en": "Justified rows",
        "fr": "Lignes justifiées",
        "es": "Líneas justificadas",
        "de": "Ausgerichtete Linien"
    },
    "layout_grid": {
        "en": "Regular grid",
        "fr": "Grille régulière",
        "es": "Cuadrícula regular",
        "de": "Regelmäßiges Raster"
    },
    "layout_v_strip": {
        "en": "Vertical strips",
        "fr": "Bandes verticales",
        "es": "Bandas verticales",
        "de": "Vertikale Streifen"
    },
    "layout_h_strip": {
        "en": "Horizontal strips",
        "fr": "Bandes horizontales",
        "es": "Bandas horizontales",
        "de": "Horizontale Streifen"
    },
    "layout_optimal": {
        "en": "Maximum optimization",
        "fr": "Optimisation maximale",
        "es": "Optimización máxima",
        "de": "Maximale Optimierung"
    },
    "btn_auto_arrange": {
        "en": "Auto-arrange",
        "fr": "Auto-organiser",
        "es": "Auto-organizar",
        "de": "Auto-Anordnung"
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
        "en": "Remove image",
        "fr": "Supprimer l'image",
        "es": "Eliminar imagen",
        "de": "Bild entfernen"
    },
    "chk_show_monitors": {
        "en": "Screen frames",
        "fr": "Cadres des écrans",
        "es": "Marcos de las pantallas",
        "de": "Bildschirmrahmen"
    },
    "btn_apply": {
        "en": "Apply wallpaper",
        "fr": "Appliquer le fond d'écran",
        "es": "Aplicar como fondo",
        "de": "Hintergrund setzen"
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
        "fr": "Fond d'écran appliqué sur chaque écran !",
        "es": "¡Fondo de pantalla aplicado a pantallas específicas!",
        "de": "Hintergrundbild erfolgreich angewendet!"
    },
    "err_api_fail": {
        "en": "Windows API failed. The wallpaper might not be applied correctly.",
        "fr": "Échec de l'API Windows. Le fond n'a peut-être pas été appliqué.",
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
        "en": "Language / Langue",
        "fr": "Langue / Language",
        "es": "Idioma / Language",
        "de": "Sprache / Language"
    },
    "btn_kofi": {
        "en": "☕ Buy me a Ko-fi",
        "fr": "☕ M'offrir un Ko-fi",
        "es": "☕ Cómprame un Ko-fi",
        "de": "☕ Ko-fi spendieren"
    },
    "lbl_simulated_view": {
        "en": "Real-world View",
        "fr": "Vue Simulée",
        "es": "Vista Real",
        "de": "Reale Ansicht"
    },
    "error_title": {
        "en": "Error",
        "fr": "Erreur",
        "es": "Error",
        "de": "Fehler"
    },
    "info_title": {
        "en": "Information",
        "fr": "Information",
        "es": "Información",
        "de": "Information"
    },
    "filetype_images": {
        "en": "Images",
        "fr": "Images",
        "es": "Imágenes",
        "de": "Bilder"
    }
}

def detect_os_language():
    """Detect default OS language, fallback to English."""
    try:
        kernel32 = ctypes.windll.kernel32
        buffer = ctypes.create_unicode_buffer(85)
        if kernel32.GetUserDefaultLocaleName(buffer, len(buffer)):
            lang_code = buffer.value.split("-")[0].lower()
            if lang_code in LANGUAGES:
                return lang_code
    except Exception:
        pass

    try:
        lang_code = locale.getlocale()[0]
        if lang_code:
            lang_code = lang_code.split("_")[0].lower()
            if lang_code in LANGUAGES:
                return lang_code
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
