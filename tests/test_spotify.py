"""Paginación de playlists y de sus temas, con una API simulada."""
from musictime import spotify as sp


def _pagina(items, total, query):
    desde = query["offset"]
    trozo = items[desde:desde + query["limit"]]
    return {"items": trozo, "next": "x" if desde + len(trozo) < total else None}


def _tema(n):
    return {"track": {"uri": f"spotify:track:{n}", "name": f"t{n}"}}


def test_playlist_tracks_trae_las_500(monkeypatch):
    todos = [_tema(n) for n in range(500)]
    pedidos = []

    def api(method, path, body=None, query=None):
        pedidos.append(query["offset"])
        return _pagina(todos, 500, query)

    monkeypatch.setattr(sp, "api", api)
    assert len(sp.playlist_tracks("p1")) == 500
    assert pedidos == [0, 100, 200, 300, 400]


def test_playlist_tracks_respeta_max_items(monkeypatch):
    todos = [_tema(n) for n in range(500)]
    monkeypatch.setattr(sp, "api", lambda m, p, body=None, query=None: _pagina(todos, 500, query))
    assert len(sp.playlist_tracks("p1", 60)) == 60


def test_playlist_tracks_descarta_locales_y_episodios(monkeypatch):
    items = [_tema(1), {"track": {"uri": "spotify:local:x", "name": "local"}},
             {"track": None}, {"track": {"uri": "spotify:episode:e", "name": "ep"}}, _tema(2)]
    monkeypatch.setattr(sp, "api", lambda m, p, body=None, query=None: _pagina(items, 5, query))
    assert [t["name"] for t in sp.playlist_tracks("p1")] == ["t1", "t2"]


def test_playlist_tracks_cae_a_items_si_tracks_falla(monkeypatch):
    rutas = []

    def api(method, path, body=None, query=None):
        rutas.append(path)
        if path.endswith("/tracks"):
            raise sp.SpotifyError("no")
        return _pagina([_tema(1)], 1, query)

    monkeypatch.setattr(sp, "api", api)
    assert len(sp.playlist_tracks("p1")) == 1
    assert rutas == ["/playlists/p1/tracks", "/playlists/p1/items"]


def test_playlists_pagina_de_a_50(monkeypatch):
    todas = [{"id": str(n)} for n in range(120)]
    monkeypatch.setattr(sp, "api", lambda m, p, body=None, query=None: _pagina(todas, 120, query))
    assert len(sp.playlists()) == 120
