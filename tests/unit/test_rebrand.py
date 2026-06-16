"""
Rebranding BandFlow (Fase 13, T-082): la marca VISIBLE es BandFlow, no ChordFlow.

Cubre que ninguna página servida ni el manifest muestren la marca antigua. La marca técnica
(título de la API, clave del service worker, comentarios) se difiere a propósito y no se comprueba aquí.
"""

import json
import pathlib

import pytest

pytestmark = pytest.mark.unit

STATIC = pathlib.Path(__file__).resolve().parents[2] / "static"


def test_sin_chordflow_visible_en_html():
    offenders = []
    for f in sorted(STATIC.glob("*.html")):
        if "_diseno" in f.name:
            continue
        if "ChordFlow" in f.read_text(encoding="utf-8"):
            offenders.append(f.name)
    assert not offenders, f"Marca antigua 'ChordFlow' visible en: {offenders}"


def test_manifest_es_bandflow():
    m = json.loads((STATIC / "manifest.json").read_text(encoding="utf-8"))
    assert m["name"] == "BandFlow" and m["short_name"] == "BandFlow"
    assert "ChordFlow" not in json.dumps(m)
