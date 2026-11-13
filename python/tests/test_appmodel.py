"""Version Microsoft Store (paquet MSIX) : dossiers réels et lancement au démarrage."""
import os
import sys
import tempfile
import unittest
from unittest import mock

import appmodel
import services


class DataRootTests(unittest.TestCase):
    def test_hors_paquet_dossier_habituel(self):
        self.assertEqual(appmodel.data_root("C:/Users/p/AppData/Local", family=""), "C:/Users/p/AppData/Local")

    def test_dans_un_paquet_chemin_reel_du_dossier_redirige(self):
        root = appmodel.data_root("C:/Users/p/AppData/Local", family="Rangorn.WallCraftPro_abc123")
        self.assertEqual(root.replace("\\", "/"),
                         "C:/Users/p/AppData/Local/Packages/Rangorn.WallCraftPro_abc123/LocalCache/Local")

    def test_reglages_de_l_exe_repris_une_seule_fois(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"LOCALAPPDATA": tmp}), \
                mock.patch.object(appmodel, "package_family_name", return_value="Fam_x"):
            os.makedirs(os.path.join(tmp, "WallCraft"))
            with open(os.path.join(tmp, "WallCraft", "settings.json"), "w", encoding="utf-8") as f:
                f.write('{"lang": "de"}')
            path = appmodel.app_data_dir()
            self.assertIn(os.path.join("Packages", "Fam_x", "LocalCache", "Local"), path)
            with open(os.path.join(path, "settings.json"), encoding="utf-8") as f:
                self.assertEqual(f.read(), '{"lang": "de"}')
            # Les réglages propres à la version Store ne sont plus écrasés ensuite.
            with open(os.path.join(path, "settings.json"), "w", encoding="utf-8") as f:
                f.write('{"lang": "fr"}')
            appmodel.app_data_dir()
            with open(os.path.join(path, "settings.json"), encoding="utf-8") as f:
                self.assertEqual(f.read(), '{"lang": "fr"}')

    def test_les_fonds_vont_dans_le_dossier_reel(self):
        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch.dict(os.environ, {"LOCALAPPDATA": tmp}), \
                mock.patch.object(appmodel, "package_family_name", return_value="Fam_x"):
            store = services.ConfigStore()
            self.assertTrue(store.root.startswith(os.path.join(tmp, "Packages", "Fam_x")))


class AutostartTests(unittest.TestCase):
    def test_hors_windows_ou_hors_paquet_pas_de_paquet(self):
        appmodel.package_family_name.cache_clear()
        self.assertFalse(appmodel.is_packaged())  # tests lancés depuis les sources

    @unittest.skipUnless(sys.platform == "win32", "Windows uniquement")
    def test_dans_un_paquet_la_tache_de_demarrage_remplace_le_registre(self):
        with mock.patch.object(appmodel, "is_packaged", return_value=True), \
                mock.patch.object(appmodel, "get_startup_task_enabled", return_value=True) as get, \
                mock.patch.object(appmodel, "set_startup_task_enabled", return_value=True) as set_:
            self.assertTrue(services.get_autostart())
            services.set_autostart(False)
            get.assert_called_once()
            set_.assert_called_once_with(False)

    @unittest.skipUnless(sys.platform == "win32", "Windows uniquement")
    def test_projection_winrt_installee(self):
        from winrt.windows.applicationmodel import StartupTask, StartupTaskState
        self.assertEqual(int(StartupTaskState.ENABLED), 2)
        self.assertTrue(hasattr(StartupTask, "get_for_current_package_async"))


if __name__ == "__main__":
    unittest.main()
