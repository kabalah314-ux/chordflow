"""
Tests de la lógica del SyncEngine ejecutándola en el navegador (T-040).
`SyncEngine` es global en index.html (carga sync_engine.js). Verificamos los casos borde de
`findActiveChord`: reset (antes del primer acorde), avance normal, empates y persistencia del
último acorde hasta el final.
"""

import pytest

pytestmark = pytest.mark.e2e


@pytest.fixture()
def sync_page(page, live_server):
    page.goto(live_server + "/static/index.html", wait_until="networkidle")
    return page


def _find_active(page, flat_chords, beat):
    """Crea un SyncEngine, le inyecta una lista plana de acordes y consulta findActiveChord."""
    return page.evaluate(
        """([chords, beat]) => {
            const e = new SyncEngine();
            e.state.flatChords = chords;
            return e.findActiveChord(beat);
        }""",
        [flat_chords, beat],
    )


def test_findactivechord_casos_borde(sync_page):
    chords = [
        {"id": "a", "absoluteBeatStart": 0.0, "duration": 4},
        {"id": "b", "absoluteBeatStart": 4.0, "duration": 4},
        {"id": "c", "absoluteBeatStart": 8.0, "duration": 4},
    ]
    # Reset: antes del primer acorde (beat negativo) → null
    assert _find_active(sync_page, chords, -1) is None
    # Inicio exacto del primero → 'a'
    assert _find_active(sync_page, chords, 0.0) == "a"
    # En medio del segundo → 'b'
    assert _find_active(sync_page, chords, 5.5) == "b"
    # Último acorde PERSISTE mucho más allá de start+duration (antes daba null) → 'c'
    assert _find_active(sync_page, chords, 999) == "c"


def test_findactivechord_empate_de_inicio(sync_page):
    """Dos acordes con el mismo beat de inicio: gana el último (no se 'saltan')."""
    chords = [
        {"id": "x", "absoluteBeatStart": 0.0, "duration": 2},
        {"id": "y", "absoluteBeatStart": 2.0, "duration": 2},
        {"id": "z", "absoluteBeatStart": 2.0, "duration": 2},  # empata con 'y'
    ]
    assert _find_active(sync_page, chords, 2.0) == "z"
    assert _find_active(sync_page, chords, 0.5) == "x"
