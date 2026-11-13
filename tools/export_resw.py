#!/usr/bin/env python3
"""Genere les fichiers .resw (WinUI 3) a partir de locales.py et ui_text.py.

Usage : python3 tools/export_resw.py
Sortie : csharp/src/WallCraft.App/Strings/<culture>/Resources.resw
"""
import os
import string
import sys
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

import locales  # noqa: E402
import ui_text  # noqa: E402

CULTURES = {"en": "en-US", "fr": "fr-FR", "es": "es-ES", "de": "de-DE"}
OUT_DIR = os.path.join(ROOT, "csharp", "src", "WallCraft.App", "Strings")
APP_NAME = "WallCraft Pro"

HEADER = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <xsd:schema id="root" xmlns="" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:msdata="urn:schemas-microsoft-com:xml-msdata">
    <xsd:import namespace="http://www.w3.org/XML/1998/namespace" />
    <xsd:element name="root" msdata:IsDataSet="true">
      <xsd:complexType>
        <xsd:choice maxOccurs="unbounded">
          <xsd:element name="metadata">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" />
              </xsd:sequence>
              <xsd:attribute name="name" use="required" type="xsd:string" />
              <xsd:attribute name="type" type="xsd:string" />
              <xsd:attribute name="mimetype" type="xsd:string" />
              <xsd:attribute ref="xml:space" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="assembly">
            <xsd:complexType>
              <xsd:attribute name="alias" type="xsd:string" />
              <xsd:attribute name="name" type="xsd:string" use="required" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="data">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
                <xsd:element name="comment" type="xsd:string" minOccurs="0" msdata:Ordinal="2" />
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" msdata:Ordinal="1" />
              <xsd:attribute name="type" type="xsd:string" msdata:Ordinal="3" />
              <xsd:attribute name="mimetype" type="xsd:string" msdata:Ordinal="4" />
              <xsd:attribute ref="xml:space" />
            </xsd:complexType>
          </xsd:element>
          <xsd:element name="resheader">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:element name="value" type="xsd:string" minOccurs="0" msdata:Ordinal="1" />
              </xsd:sequence>
              <xsd:attribute name="name" type="xsd:string" use="required" />
            </xsd:complexType>
          </xsd:element>
        </xsd:choice>
      </xsd:complexType>
    </xsd:element>
  </xsd:schema>
  <resheader name="resmimetype">
    <value>text/microsoft-resx</value>
  </resheader>
  <resheader name="version">
    <value>2.0</value>
  </resheader>
  <resheader name="reader">
    <value>System.Resources.ResXResourceReader, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>
  </resheader>
  <resheader name="writer">
    <value>System.Resources.ResXResourceWriter, System.Windows.Forms, Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value>
  </resheader>
"""


def convert_markers(text, where):
    """Convertit les {} positionnels Python en {0}, {1}... (accolades litterales gardees doublees)."""
    out = []
    index = 0
    try:
        parsed = list(string.Formatter().parse(text))
    except ValueError as exc:
        raise ValueError("%s : format invalide (%s) : %r" % (where, exc, text))
    for literal, field, spec, conv in parsed:
        out.append(literal.replace("{", "{{").replace("}", "}}"))
        if field is None:
            continue
        if field != "" or spec or conv:
            raise ValueError("%s : marqueur non positionnel simple {} non gere : %r" % (where, text))
        out.append("{%d}" % index)
        index += 1
    return "".join(out)


def collect():
    """Retourne {cle: (source, {lang: valeur})} ; ui_text l'emporte sur locales."""
    entries = {}
    duplicates = set()
    for key, per_lang in locales._STRINGS.items():
        entries[key] = ("locales.py", per_lang)
    for key, per_lang in ui_text.UI_TEXT.items():
        if key in entries:
            duplicates.add(key)
        entries[key] = ("ui_text.py", per_lang)
    return entries, duplicates


def build_resources(entries, duplicates):
    """Retourne {lang: [(nom, valeur, commentaire ou None), ...]} trie par nom."""
    result = {lang: [] for lang in CULTURES}
    for key, (_source, per_lang) in entries.items():
        dup_comment = None
        if key in duplicates:
            dup_comment = "Defined in both locales.py and ui_text.py; ui_text.py wins."
        is_plural = [isinstance(per_lang.get(lang), tuple) for lang in CULTURES if lang in per_lang]
        if any(is_plural) and not all(is_plural):
            raise ValueError("%s : pluriel dans certaines langues seulement" % key)
        plural = bool(is_plural) and all(is_plural)
        for lang in CULTURES:
            missing = lang not in per_lang
            value = per_lang["en"] if missing else per_lang[lang]
            comments = []
            if dup_comment:
                comments.append(dup_comment)
            if missing:
                comments.append("MISSING:%s" % lang)
            comment = " ".join(comments) or None
            if plural:
                one, other = value
                result[lang].append((key + "_One", convert_markers(one, key + "/" + lang), comment))
                result[lang].append((key + "_Other", convert_markers(other, key + "/" + lang), comment))
            else:
                result[lang].append((key, convert_markers(value, key + "/" + lang), comment))
    for lang in CULTURES:
        result[lang].append(("AppDisplayName", APP_NAME, None))
        result[lang].sort(key=lambda item: item[0])
        names = [item[0] for item in result[lang]]
        if len(names) != len(set(names)):
            raise ValueError("noms de ressources en collision (%s)" % lang)
    return result


def render(resources):
    parts = [HEADER]
    for name, value, comment in resources:
        parts.append('  <data name="%s" xml:space="preserve">\n' % escape(name, {'"': "&quot;"}))
        parts.append("    <value>%s</value>\n" % escape(value))
        if comment:
            parts.append("    <comment>%s</comment>\n" % escape(comment))
        parts.append("  </data>\n")
    parts.append("</root>\n")
    return "".join(parts)


def main():
    entries, duplicates = collect()
    result = build_resources(entries, duplicates)
    for lang, culture in CULTURES.items():
        folder = os.path.join(OUT_DIR, culture)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "Resources.resw")
        with open(path, "w", encoding="utf-8-sig", newline="\n") as handle:
            handle.write(render(result[lang]))
        print("%s : %d ressources" % (os.path.relpath(path, ROOT), len(result[lang])))
    plurals = sum(1 for key, (_s, d) in entries.items() if isinstance(next(iter(d.values())), tuple))
    print("%d cles, %d pluriels, %d doublons %s" % (len(entries), plurals, len(duplicates), sorted(duplicates) or ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
