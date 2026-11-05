"""Copia de seguridad de la base de datos de producción (T-V6-72).

Uso:  DATABASE_URL=postgresql://… python harness/backup_db.py
Deja `backups/bandflow-AAAAMMDD-HHMM.dump` (formato custom de pg_dump, restaurable con pg_restore).
Requiere `pg_dump` instalado. No imprime la URL (lleva la contraseña).
"""

import datetime as _dt
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith("postgres"):
        print("Falta DATABASE_URL de Postgres (pooler de sesión, puerto 5432).")
        return 2
    out = Path(__file__).resolve().parent.parent / "backups"
    out.mkdir(exist_ok=True)
    name = out / f"bandflow-{_dt.datetime.now():%Y%m%d-%H%M}.dump"
    res = subprocess.run(["pg_dump", "--format=custom", "--no-owner", "--no-privileges",
                          f"--file={name}", url], capture_output=True, text=True)
    if res.returncode != 0:
        print("pg_dump falló:", res.stderr.replace(url, "***")[:500])
        return res.returncode
    print(f"OK: {name} ({name.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
