"""Búsqueda de letras en LRCLIB y caché, con la API simulada."""
import time

import pytest

from musictime import lyrics as ly


def _tema(name="Song", artists=("A",), secs=200):
    return {"uri": f"spotify:track:{name}", "name": name, "duration_ms": secs * 1000,
            "artists": [{"name": a} for a in artists], "album": {"name": "Album"}}


@pytest.fixture(autouse=True)
def cache(tmp_path, monkeypatch):
    monkeypatch.setattr(ly, "CACHE_DIR", str(tmp_path))


@pytest.mark.parametrize("name, clean", [
    ("Let It Be - Remastered 2009", "Let It Be"),
    ("Song (feat. X & Y)", "Song"),
    ("Song [with Z] - Live at Wembley", "Song"),
    ("Hey Jude - 2015 Mix", "Hey Jude"),
    ("Persiana Americana - En Vivo", "Persiana Americana"),
    ("Mr. Brightside", "Mr. Brightside"),
    ("Bohemian Rhapsody - Rock Band", "Bohemian Rhapsody - Rock Band"),
])
def test_clean_title(name, clean):
    assert ly.clean_title(name) == clean


def test_busca_con_titulo_limpio_y_segundo_artista(monkeypatch):
    pedidos = []

    def get(path, query):
        pedidos.append((path, query))
        if path == "search" and query.get("track_name") == "Song" and query.get("artist_name") == "B":
            return [{"duration": 250, "plainLyrics": "no"},
                    {"duration": 201, "plainLyrics": "x"},
                    {"duration": 199, "syncedLyrics": "[00:01.00] hola", "plainLyrics": "hola"}]
        return None

    monkeypatch.setattr(ly, "_get", get)
    out = ly.fetch(_tema("Song - Remastered", ("A", "B")))
    assert out["synced"] == [(1000, "hola")]
    assert ("get", {"track_name": "Song", "artist_name": "A", "duration": 200}) in pedidos


def test_no_encontre_vence_y_se_reintenta(monkeypatch):
    llamadas = []
    monkeypatch.setattr(ly, "_get", lambda p, q: llamadas.append(p) and None)
    ly.fetch(_tema())
    n = len(llamadas)
    ly.fetch(_tema())
    assert len(llamadas) == n  # dentro del día: sale de la caché
    monkeypatch.setattr(time, "time", lambda: 10**12)
    ly.fetch(_tema())
    assert len(llamadas) == 2 * n


def test_acierto_queda_en_cache(monkeypatch):
    monkeypatch.setattr(ly, "_get", lambda p, q: {"plainLyrics": "hola"})
    ly.fetch(_tema())
    monkeypatch.setattr(ly, "_get", lambda p, q: pytest.fail("no debería pedir"))
    monkeypatch.setattr(time, "time", lambda: 10**12)
    assert ly.fetch(_tema())["plain"] == "hola"


def test_error_de_red_no_se_guarda(monkeypatch, tmp_path):
    def caido(p, q):
        raise TimeoutError
    monkeypatch.setattr(ly, "_get", caido)
    with pytest.raises(TimeoutError):
        ly.fetch(_tema())
    assert not list(tmp_path.iterdir())
