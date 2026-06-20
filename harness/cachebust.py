"""
cachebust.py — Cache-busting automático por hash de contenido (T-022).

Sustituye el `?v=N` manual (que había que subir a mano en cada `.html` y "mordió" varias veces)
por un hash del contenido real del fichero. Así la versión SIEMPRE corresponde al contenido:
si cambia el `.js`/`.css`, cambia el hash; si no, no.

Uso:
    python harness/cachebust.py            # reescribe los ?v= de TODOS los static/*.html
    python harness/cachebust.py --check    # NO escribe; sale 1 si algún ?v= está desactualizado

Solo toca referencias a ficheros LOCALES de `static/` (ignora URLs http(s) como el CDN/fuentes).
La función `check()` la usa un test del harness para que `run_checks` falle si alguien edita un
asset sin reejecutar este script.
"""

import hashlib
import re
import sys
from pathlib import Path

# UTF-8 en la salida: la consola de Windows (cp1252) revienta con los emojis del resumen.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"

# Captura  src="archivo.js?v=..."  o  href="archivo.css?v=..."  (comillas dobles).
_REF = re.compile(r'(?P<attr>\b(?:src|href))="(?P<file>[^"?]+\.(?:js|css))(?:\?v=[^"]*)?"')


def _hash(path: Path) -> str:
    """Hash corto (sha256[:8]) del contenido del fichero.

    Normaliza el fin de línea (CRLF/CR → LF) antes de hashear: así el `?v=` es el MISMO en
    cualquier checkout (Windows/Mac/Linux) y no depende de cómo git materialice los saltos de
    línea. Sin esto, un `?v=` generado en una copia CRLF rompía el test en checkouts LF (y en CI).
    """
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()[:8]


def _process(html_text: str):
    """Devuelve (texto_reescrito, lista_de_desajustes). Un desajuste es un ref local cuyo
    ?v= no coincide con el hash actual del fichero."""
    mismatches = []

    def repl(m):
        ref = m.group("file")
        # Ignorar URLs absolutas (CDN, fuentes): no son ficheros locales.
        if "://" in ref:
            return m.group(0)
        asset = STATIC / ref
        if not asset.exists():
            return m.group(0)  # referencia desconocida: no tocar
        h = _hash(asset)
        nuevo = f'{m.group("attr")}="{ref}?v={h}"'
        if nuevo != m.group(0):
            mismatches.append(ref)
        return nuevo

    return _REF.sub(repl, html_text), mismatches


def check() -> list[str]:
    """Sin escribir: devuelve la lista de referencias (html::asset) con hash desactualizado."""
    stale = []
    for html in sorted(STATIC.glob("*.html")):
        _, mism = _process(html.read_text(encoding="utf-8"))
        stale += [f"{html.name}::{r}" for r in mism]
    return stale


def apply() -> list[str]:
    """Reescribe los ?v= en su sitio. Devuelve la lista de ficheros HTML modificados."""
    cambiados = []
    for html in sorted(STATIC.glob("*.html")):
        original = html.read_text(encoding="utf-8")
        nuevo, mism = _process(original)
        if mism:
            html.write_text(nuevo, encoding="utf-8")
            cambiados.append(html.name)
    return cambiados


def main(argv) -> int:
    if "--check" in argv:
        stale = check()
        if stale:
            print("❌ Cache-busting desactualizado en:")
            for s in stale:
                print(f"   - {s}")
            print("Ejecuta: python harness/cachebust.py")
            return 1
        print("✅ Cache-busting al día (todos los ?v= coinciden con el contenido).")
        return 0
    cambiados = apply()
    print("Reescritos: " + (", ".join(cambiados) if cambiados else "ninguno (ya al día)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
