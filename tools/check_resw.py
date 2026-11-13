#!/usr/bin/env python3
"""Verifie la coherence des 4 fichiers Resources.resw generes par export_resw.py."""
import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRINGS = os.path.join(ROOT, "csharp", "src", "WallCraft.App", "Strings")
CULTURES = ["en-US", "fr-FR", "es-ES", "de-DE"]
MARKER = re.compile(r"(?<!\{)(?:\{\{)*\{(\d+)\}")


def load(culture, errors):
    path = os.path.join(STRINGS, culture, "Resources.resw")
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as exc:
        errors.append("%s : impossible de lire le XML (%s)" % (culture, exc))
        return None
    data = {}
    for node in tree.getroot().findall("data"):
        name = node.get("name")
        value = node.find("value")
        if name in data:
            errors.append("%s : ressource en double : %s" % (culture, name))
        data[name] = (value.text or "") if value is not None else ""
    return data


def markers(text):
    return sorted(MARKER.findall(text))


def main():
    errors = []
    loaded = {c: load(c, errors) for c in CULTURES}
    ok = {c: d for c, d in loaded.items() if d is not None}
    if ok:
        reference = set().union(*[set(d) for d in ok.values()])
        for culture, data in ok.items():
            for key in sorted(reference - set(data)):
                errors.append("%s : cle manquante : %s" % (culture, key))
            for key, value in sorted(data.items()):
                if not value.strip():
                    errors.append("%s : valeur vide : %s" % (culture, key))
        for key in sorted(reference):
            found = {c: markers(d[key]) for c, d in ok.items() if key in d}
            if len({tuple(v) for v in found.values()}) > 1:
                detail = ", ".join("%s=%s" % (c, "".join("{%s}" % m for m in v) or "aucun") for c, v in found.items())
                errors.append("marqueurs differents pour %s : %s" % (key, detail))
    if errors:
        print("%d probleme(s) :" % len(errors))
        for line in errors:
            print("  - " + line)
        return 1
    count = len(next(iter(ok.values())))
    print("OK : %d ressources identiques dans %d langues." % (count, len(ok)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
