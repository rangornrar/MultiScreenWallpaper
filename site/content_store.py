"""Accès à la version C# pendant la préparation de la première publication Store."""

BUILD_URL = "https://github.com/rangornrar/MultiScreenWallpaper/actions/workflows/csharp.yml"
RELEASES_URL = "https://github.com/rangornrar/MultiScreenWallpaper/releases"

TEXT = {
    "fr": (
        "Version C# pour Windows", "WallCraft Pro est désormais développé en C# et WinUI 3. La première publication Microsoft Store est en préparation.",
        "Essayer le build C#", "Ouvrez une exécution réussie du workflow C#, téléchargez WallCraft-win-x64, extrayez toute l’archive puis lancez WallCraft.exe.",
        "Prérequis", "PC Windows x64. Windows 11 recommandé ; minimum technique : Windows 10 version 2004, build 19041. .NET et Windows App SDK sont inclus. Python et OpenCV ne sont pas nécessaires.",
        "Archives Python", "Les anciennes releases GitHub contiennent l’implémentation Python historique. Elles ne correspondent pas à l’application C# montrée dans la démonstration.",
        "Code C# public ; version Microsoft Store en préparation. Les anciennes releases Python restent archivées sur GitHub.",
    ),
    "en": (
        "C# version for Windows", "WallCraft Pro is now built with C# and WinUI 3. Its first Microsoft Store release is being prepared.",
        "Try the C# build", "Open a successful C# workflow run, download WallCraft-win-x64, extract the entire archive, then start WallCraft.exe.",
        "Requirements", "Windows x64 PC. Windows 11 recommended; technical minimum: Windows 10 version 2004, build 19041. .NET and Windows App SDK are included. Python and OpenCV are not required.",
        "Python archives", "Older GitHub releases contain the historical Python implementation. They do not match the C# application shown in the demo.",
        "Public C# source; Microsoft Store release in preparation. Older Python releases remain archived on GitHub.",
    ),
    "es": (
        "Versión C# para Windows", "WallCraft Pro ahora está desarrollado en C# y WinUI 3. La primera publicación en Microsoft Store está en preparación.",
        "Probar la compilación C#", "Abra una ejecución correcta del flujo C#, descargue WallCraft-win-x64, extraiga todo el archivo e inicie WallCraft.exe.",
        "Requisitos", "PC Windows x64. Windows 11 recomendado; mínimo técnico: Windows 10 versión 2004, compilación 19041. Incluye .NET y Windows App SDK. No requiere Python ni OpenCV.",
        "Archivos Python", "Las antiguas versiones de GitHub contienen la implementación histórica en Python. No corresponden a la aplicación C# de la demostración.",
        "Código C# público; publicación en Microsoft Store en preparación. Las antiguas versiones Python siguen archivadas en GitHub.",
    ),
    "de": (
        "C#-Version für Windows", "WallCraft Pro wird jetzt mit C# und WinUI 3 entwickelt. Die erste Veröffentlichung im Microsoft Store wird vorbereitet.",
        "C#-Build ausprobieren", "Öffnen Sie einen erfolgreichen C#-Workflow-Lauf, laden Sie WallCraft-win-x64 herunter, entpacken Sie das gesamte Archiv und starten Sie WallCraft.exe.",
        "Voraussetzungen", "Windows-PC mit x64. Windows 11 empfohlen; technisches Minimum: Windows 10 Version 2004, Build 19041. .NET und Windows App SDK sind enthalten. Python und OpenCV sind nicht erforderlich.",
        "Python-Archiv", "Ältere GitHub-Releases enthalten die frühere Python-Implementierung. Sie entsprechen nicht der C#-Anwendung im Demovideo.",
        "Öffentlicher C#-Quellcode; Microsoft-Store-Veröffentlichung in Vorbereitung. Frühere Python-Releases bleiben auf GitHub archiviert.",
    ),
}


def apply(pages, languages, previous_download):
    for lang, text in TEXT.items():
        title, lead, build_title, build_body, requirements, requirements_body, archive_title, archive_body, footer = text
        languages[lang]["download_now"] = build_title
        languages[lang]["footer_source_text"] = footer
        for page in pages[lang].values():
            for section in page.get("sections", []):
                for card in section.get("cards", []):
                    if card.get("url") == previous_download:
                        card.update(url=BUILD_URL, title=build_title, text=build_body, cta=build_title)
                if section.get("type") == "faq":
                    section["items"] = [
                        (question, archive_body + " " + build_body)
                        if "release" in question.lower() else (question, answer)
                        for question, answer in section.get("items", [])
                    ]
        pages[lang]["home"]["hero_lead"] = lead
        pages[lang]["download"] = {
            "meta_title": title + " — WallCraft Pro",
            "meta_description": requirements_body,
            "hero_badge": "C# / WinUI 3",
            "hero_title": title,
            "hero_lead": lead,
            "sections": [
                {"type": "cards", "title": build_title, "text": "", "cards": [
                    {"title": build_title, "text": build_body, "url": BUILD_URL, "cta": build_title},
                    {"title": archive_title, "text": archive_body, "url": RELEASES_URL, "cta": archive_title},
                ]},
                {"type": "text", "title": requirements, "text": requirements_body, "body": []},
                {"type": "links", "title": languages[lang]["related_title"], "text": "", "links": ["help", "how-it-works", "privacy"]},
            ],
        }
