# appmodel.py
"""
Ce qui change quand WallCraft tourne dans un paquet MSIX (version Microsoft Store).

Dans un paquet, Windows redirige vers un dossier privé les écritures dans
%LOCALAPPDATA% et dans HKCU. Deux conséquences :

- les images appliquées comme fond d'écran doivent être désignées par leur chemin
  réel (le dossier « Packages\\<famille>\\LocalCache\\Local ») : l'Explorateur, qui
  affiche le fond, ne voit pas la vue redirigée ;
- la clé HKCU\\...\\Run est ignorée : le lancement au démarrage passe par la
  tâche de démarrage déclarée dans le manifeste (StartupTask), que l'utilisateur
  retrouve aussi dans Paramètres > Applications > Démarrage. Windows ne passe pas
  d'argument « --tray » à ce lancement : WallCraft le reconnaît à son type d'activation.

Hors paquet (exe de GitHub, sources), tout reste comme avant.
"""
import functools
import os
import shutil
import sys

STARTUP_TASK_ID = "WallCraftStartup"  # identique au TaskId du manifeste MSIX
_NO_PACKAGE = 15700                   # APPMODEL_ERROR_NO_PACKAGE
_INSUFFICIENT_BUFFER = 122


@functools.lru_cache(maxsize=1)
def package_family_name():
    """Nom de famille du paquet MSIX en cours, ou None hors paquet."""
    if sys.platform != "win32":
        return None
    import ctypes
    try:
        fn = ctypes.windll.kernel32.GetCurrentPackageFamilyName
    except AttributeError:  # Windows trop ancien
        return None
    length = ctypes.c_uint32(0)
    if fn(ctypes.byref(length), None) != _INSUFFICIENT_BUFFER:
        return None
    buf = ctypes.create_unicode_buffer(length.value)
    if fn(ctypes.byref(length), buf) != 0:
        return None
    return buf.value or None


def is_packaged():
    return package_family_name() is not None


def _local_app_data():
    return os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), ".local", "share")


def data_root(local_app_data=None, family=None):
    """Dossier qui contient « WallCraft » : %LOCALAPPDATA% ou son équivalent réel dans le paquet."""
    base = local_app_data or _local_app_data()
    family = family if family is not None else package_family_name()
    if family:
        return os.path.join(base, "Packages", family, "LocalCache", "Local")
    return base


def app_data_dir():
    path = os.path.join(data_root(), "WallCraft")
    os.makedirs(path, exist_ok=True)
    if is_packaged():
        _import_settings_once(path)
    return path


def _import_settings_once(path):
    """Première ouverture de la version Store : reprend les réglages de l'exe GitHub s'ils existent."""
    target = os.path.join(path, "settings.json")
    if os.path.exists(target):
        return
    source = os.path.join(_local_app_data(), "WallCraft", "settings.json")
    if os.path.normcase(os.path.abspath(source)) == os.path.normcase(os.path.abspath(target)):
        return
    try:
        shutil.copyfile(source, target)
    except OSError:
        pass


# --- Lancement au démarrage dans un paquet (StartupTask) ---

_ENABLED_STATES = (2, 4)      # Enabled, EnabledByPolicy
_DISABLED_BY_USER = 1
_ACTIVATION_STARTUP_TASK = 1020


def activation_kind():
    """Type d'activation du paquet (ActivationKind), ou None hors paquet ou en cas d'erreur."""
    if not is_packaged():
        return None
    try:
        from winrt.windows.applicationmodel import AppInstance
        args = AppInstance.get_activated_event_args()
        return int(args.kind) if args is not None else None
    except Exception:
        return None


def launched_at_startup():
    """True si Windows a lancé WallCraft par la tâche de démarrage (ouverture dans la zone de notification)."""
    return activation_kind() == _ACTIVATION_STARTUP_TASK


def _run(awaitable):
    import asyncio
    async def wait():
        return await awaitable
    return asyncio.run(wait())


def _startup_task():
    from winrt.windows.applicationmodel import StartupTask
    for task in _run(StartupTask.get_for_current_package_async()):
        if task.task_id == STARTUP_TASK_ID:
            return task
    raise OSError(f"La tâche de démarrage {STARTUP_TASK_ID} est absente du paquet.")


def get_startup_task_enabled():
    try:
        return int(_startup_task().state) in _ENABLED_STATES
    except Exception:
        return False


def set_startup_task_enabled(enabled):
    """
    Active ou désactive la tâche de démarrage. Si l'utilisateur l'a désactivée dans les
    Paramètres de Windows, seul lui peut la réactiver : on ouvre alors la page Démarrage.
    """
    try:
        task = _startup_task()
        if not enabled:
            task.disable()
            return True
        state = int(_run(task.request_enable_async()))
    except OSError:
        raise
    except Exception as e:
        raise OSError(str(e)) from e
    if state in _ENABLED_STATES:
        return True
    if state == _DISABLED_BY_USER:
        open_startup_settings()
    return False


def open_startup_settings():
    try:
        os.startfile("ms-settings:startupapps")
    except (OSError, AttributeError):
        pass


# --- Vérification automatique du paquet (CI) ---

def selftest(report_path):
    """
    Lancé par « WallCraft.exe --selftest <fichier> » dans le paquet installé, sur le runner
    Windows de la CI : vérifie le dossier réel, l'application d'un fond depuis ce dossier
    et la tâche de démarrage, puis écrit le résultat en JSON.
    """
    import json
    import traceback
    report = {"packaged": is_packaged(), "family": package_family_name()}
    try:
        from PIL import Image
        import screen_splitter
        folder = app_data_dir()
        report["data_dir"] = folder
        image = os.path.join(folder, "selftest.png")
        Image.new("RGB", (64, 36), (40, 90, 160)).save(image, "PNG")
        report["wallpaper_set"] = screen_splitter.set_wallpaper_span(image)
        report["wallpaper_now"] = [w["path"] for w in screen_splitter.get_current_wallpapers()]
        report["activation_kind"] = activation_kind()
        try:
            from winrt.windows.applicationmodel import AppInstance
            args = AppInstance.get_activated_event_args()
            report["activation_args"] = repr(args)
        except Exception:
            report["activation_error"] = traceback.format_exc()
        report["launched_at_startup"] = launched_at_startup()
        from winrt.windows.applicationmodel import StartupTask
        report["startup_tasks"] = [t.task_id for t in _run(StartupTask.get_for_current_package_async())]
        report["startup_before"] = get_startup_task_enabled()
        report["startup_enable"] = set_startup_task_enabled(True)
        report["startup_after_enable"] = get_startup_task_enabled()
        set_startup_task_enabled(False)
        report["startup_after_disable"] = get_startup_task_enabled()
    except Exception:
        report["error"] = traceback.format_exc()
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
