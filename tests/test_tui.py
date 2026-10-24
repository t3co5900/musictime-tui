"""Prueba de humo del dashboard con la API simulada (no toca Spotify)."""
import asyncio

from musictime import spotify as sp
from musictime.tui import MusicTime

TRACK = {"name": "Tema", "uri": "spotify:track:1", "artists": [{"name": "Artista"}],
         "album": {"name": "Álbum"}, "duration_ms": 200000}
STATE = {"is_playing": True, "progress_ms": 60000, "shuffle_state": False, "repeat_state": "off",
         "item": TRACK, "device": {"name": "Mac", "volume_percent": 40}}


def test_dashboard(monkeypatch):
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    calls = []
    monkeypatch.setattr(sp, "playback", lambda: STATE)
    monkeypatch.setattr(sp, "playlists", lambda: [])
    monkeypatch.setattr(sp, "queue", lambda: {"queue": [TRACK]})
    monkeypatch.setattr(sp, "devices", lambda: [{"id": "d1", "name": "Mac", "type": "Computer",
                                                 "is_active": True, "volume_percent": 40}])
    monkeypatch.setattr(sp, "search", lambda q, n=10: [TRACK])
    monkeypatch.setattr(sp, "pause", lambda: calls.append("pause"))
    monkeypatch.setattr(sp, "set_volume", lambda v: calls.append(("vol", v)))

    async def run():
        app = MusicTime()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            assert "Tema" in str(app.query_one("#now").render())
            await pilot.press("space")
            await pilot.press("plus")
            await pilot.pause(0.5)

    asyncio.run(run())
    assert "pause" in calls and ("vol", 45) in calls


def test_enter_reproduce_resultado(monkeypatch):
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    played = []
    monkeypatch.setattr(sp, "playback", lambda: STATE)
    monkeypatch.setattr(sp, "playlists", lambda: [])
    monkeypatch.setattr(sp, "queue", lambda: {"queue": []})
    monkeypatch.setattr(sp, "search", lambda q, n=10: [TRACK])
    monkeypatch.setattr(sp, "play_track", lambda track, context_uri=None, device=None: played.append((track["uri"], context_uri)))

    async def run():
        app = MusicTime()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("slash", "t", "e", "enter")
            await pilot.pause(0.8)
            await pilot.press("enter")
            await pilot.pause(0.8)

    asyncio.run(run())
    assert played == [("spotify:track:1", None)]


def test_playlist_abre_y_reproduce_con_su_contexto(monkeypatch):
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    played = []
    monkeypatch.setattr(sp, "playback", lambda: STATE)
    monkeypatch.setattr(sp, "queue", lambda: {"queue": []})
    monkeypatch.setattr(sp, "playlists", lambda: [{"id": "p1", "uri": "spotify:playlist:p1", "name": "Mi lista", "owner": {"id": "yo"},
                                                   "tracks": {"total": 1}}])
    monkeypatch.setattr(sp, "playlist_tracks", lambda pid: [TRACK])
    monkeypatch.setattr(sp, "play_track", lambda track, context_uri=None, device=None: played.append((track["uri"], context_uri)))

    async def run():
        app = MusicTime()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("l")
            await pilot.pause(0.6)
            await pilot.press("enter")
            await pilot.pause(0.6)
            await pilot.press("enter")
            await pilot.pause(0.6)

    asyncio.run(run())
    assert played == [("spotify:track:1", "spotify:playlist:p1")]


def test_abre_mostrando_las_playlists(monkeypatch):
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    monkeypatch.setattr(sp, "playback", lambda: STATE)
    monkeypatch.setattr(sp, "playlists", lambda: [{"id": "p1", "uri": "spotify:playlist:p1", "name": "Mi lista", "owner": {"id": "yo"},
                                                   "tracks": {"total": 3}}])

    async def run():
        app = MusicTime()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.8)
            return app.mode, app.query_one("DataTable").row_count

    assert asyncio.run(run()) == ("playlists", 1)


def test_playlist_con_temas_repetidos(monkeypatch):
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    played = []
    monkeypatch.setattr(sp, "playback", lambda: STATE)
    monkeypatch.setattr(sp, "playlists", lambda: [{"id": "p1", "uri": "spotify:playlist:p1", "name": "Mi lista", "owner": {"id": "yo"},
                                                   "tracks": {"total": 2}}])
    monkeypatch.setattr(sp, "playlist_tracks", lambda pid: [TRACK, TRACK])
    monkeypatch.setattr(sp, "play_track", lambda track, context_uri=None, device=None: played.append(track["uri"]))

    async def run():
        app = MusicTime()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.6)
            await pilot.press("enter")
            await pilot.pause(0.6)
            filas = app.query_one("DataTable").row_count
            await pilot.press("down", "enter")
            await pilot.pause(0.6)
            return filas

    assert asyncio.run(run()) == 2
    assert played == ["spotify:track:1"]


def test_search_pide_paginas_de_diez(monkeypatch):
    pedidos = []

    def falso_api(method, path, body=None, query=None):
        pedidos.append((query["limit"], query["offset"]))
        assert query["limit"] <= 10  # Spotify devuelve 400 con más de 10
        return {"tracks": {"items": [dict(TRACK, uri=f"spotify:track:{query['offset'] + i}") for i in range(query["limit"])]}}

    monkeypatch.setattr(sp, "api", falso_api)
    assert len(sp.search("x", 15)) == 15
    assert pedidos == [(10, 0), (5, 10)]


# Líneas inventadas para las pruebas (no son letras reales).
LRC_PRUEBA = "[ar:Nadie]\n[00:01.00] primera linea de prueba\n[00:05.50] segunda linea de prueba\n[00:10.00]\n[00:12.25][00:30.00] estribillo de prueba"


def test_parse_lrc():
    from musictime import lyrics as ly
    r = ly.parse_lrc(LRC_PRUEBA)
    assert r[0] == (1000, "primera linea de prueba")
    assert (5500, "segunda linea de prueba") in r and (10000, "") in r
    assert [t for t, x in r if x == "estribillo de prueba"] == [12250, 30000]
    assert [t for t, _ in r] == sorted(t for t, _ in r)


def test_pantalla_de_letra(monkeypatch):
    from musictime import lyrics as ly
    monkeypatch.setattr(sp, "playback", lambda: dict(STATE, progress_ms=6000))
    monkeypatch.setattr(sp, "playlists", lambda: [])
    monkeypatch.setattr(ly, "fetch", lambda track: {"synced": ly.parse_lrc(LRC_PRUEBA), "plain": None, "instrumental": False})

    async def run():
        app = MusicTime()
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("y")
            await pilot.pause(0.8)
            texto = str(app.screen.query_one("#l-body").render())
            await pilot.press("escape")
            await pilot.pause(0.3)
            return texto, type(app.screen).__name__

    texto, pantalla = asyncio.run(run())
    assert "segunda linea de prueba" in texto and "✦" in texto
    assert pantalla != "LyricsScreen"


def test_playlist_ajena_se_reproduce_completa(monkeypatch):
    jugadas, abiertas = [], []
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    monkeypatch.setattr(sp, "playback", lambda: STATE)
    monkeypatch.setattr(sp, "playlists", lambda: [
        {"id": "aj", "uri": "spotify:playlist:aj", "name": "De un amigo", "owner": {"id": "otro"}, "tracks": {"total": 9}}])
    monkeypatch.setattr(sp, "playlist_tracks", lambda pid: abiertas.append(pid) or [])
    monkeypatch.setattr(sp, "play_context", lambda uri, device=None: jugadas.append(uri))

    async def run():
        app = MusicTime()
        async with app.run_test(size=(120, 30)) as pilot:
            await pilot.pause(0.6)
            await pilot.press("enter")
            await pilot.pause(0.6)

    asyncio.run(run())
    assert jugadas == ["spotify:playlist:aj"] and abiertas == []  # no intenta listar los temas (daría 403)


def _imagen_prueba():
    """Degradé rojo-azul generado en el momento (no es una portada real)."""
    from PIL import Image
    im = Image.new("RGB", (64, 64))
    im.putdata([(255 - 4 * x, 40, 4 * x) for y in range(64) for x in range(64)])
    return im


def test_to_grid_bloques_y_ascii():
    from musictime import cover as cv
    g = cv.to_grid(_imagen_prueba(), 20, 10)  # bloques: cada celda lleva color arriba y fondo abajo
    assert len(g) == 10 and all(len(f) == 20 for f in g)
    ch, (r, _, b), fondo = g[0][0]
    assert ch == "▀" and r > b and fondo is not None      # izquierda: rojiza
    assert g[0][-1][1][2] > g[0][-1][1][0]                 # derecha: azulada
    a = cv.to_grid(_imagen_prueba(), 20, 10, "ascii")
    assert a[0][0][0] in cv.RAMP and a[0][0][2] is None


def test_image_url_elige_la_de_300px():
    from musictime import cover as cv
    album = {"images": [{"url": "grande", "width": 640}, {"url": "media", "width": 300}, {"url": "chica", "width": 64}]}
    assert cv.image_url(album) == "media" and cv.image_url({}) is None


def test_portada_se_deshace_y_sube_desde_abajo():
    from musictime.tui import CoverView
    vieja = [[("#", (200, 50, 50))] * 6 for _ in range(6)]
    nueva = [[("@", (50, 50, 200))] * 6 for _ in range(6)]
    v = CoverView()
    v.fijar(vieja)
    v.mostrar(nueva)
    assert v.fase == "salida"
    v.avanzar(v.SALIDA / 2)                    # a mitad: se disolvió parte, no todo
    celdas = [c for f in v.dibujar().plain.split("\n") for c in f]
    assert 0 < celdas.count(" ") < len(celdas)
    v.avanzar(v.SALIDA)                        # terminó de deshacerse y empieza a entrar la nueva
    assert v.fase == "entrada" and v.grid is nueva
    v.avanzar(v.ENTRADA * 0.4)                 # a 40%: solo las filas de abajo son visibles
    filas = v.dibujar().plain.split("\n")
    assert filas[-1].strip() and not filas[0].strip()
    v.avanzar(v.ENTRADA)
    assert v.fase == "reposo" and all(f.strip() for f in v.dibujar().plain.split("\n"))


def test_portada_nueva_espera_si_llega_tarde():
    from musictime.tui import CoverView
    v = CoverView()
    v.fijar([[("#", (9, 9, 9))] * 4] * 4)
    v.comenzar_salida()
    v.avanzar(v.SALIDA + 0.01)                 # se deshizo y todavía no llegó la nueva
    assert v.fase == "vacio"
    v.mostrar([[("@", (1, 2, 3))] * 4] * 4)    # llega tarde: entra directo
    assert v.fase == "entrada"


def test_pantalla_de_portada_carga_y_cambia_con_el_tema(monkeypatch):
    from musictime import cover as cv
    monkeypatch.setattr(sp, "me_id", lambda: "yo")
    monkeypatch.setattr(sp, "playlists", lambda: [])
    monkeypatch.setattr(sp, "queue", lambda: {"queue": []})
    album = lambda n: {"name": "A", "uri": "x", "images": [{"url": f"http://img/{n}", "width": 640}]}
    estado = {"v": dict(STATE, item=dict(TRACK, album=album(1)))}
    monkeypatch.setattr(sp, "playback", lambda: estado["v"])
    pedidas = []

    def falso_build(alb, c, f, modo="bloques"):
        pedidas.append((alb["images"][0]["url"][-1], c, f, modo))
        return [[("▀", (90, 90, 200), (20, 20, 90))] * c] * f

    monkeypatch.setattr(cv, "build", falso_build)

    async def run():
        app = MusicTime()
        async with app.run_test(size=(120, 50)) as pilot:
            await pilot.pause(0.6)
            await pilot.press("c")
            await pilot.pause(2.0)
            antes = app.screen.query_one("#c-cover").grid is not None
            medidas = app.screen.medidas
            estado["v"] = dict(STATE, item=dict(TRACK, uri="spotify:track:2", album=album(2)))
            app.refresh_state()
            await pilot.pause(3.5)
            await pilot.press("a")                      # cambia a ASCII
            await pilot.pause(0.8)
            fase = app.screen.query_one("#c-cover").fase
            await pilot.press("escape")
            await pilot.pause(0.3)
            return antes, medidas, fase, type(app.screen).__name__

    antes, medidas, fase, pantalla = asyncio.run(run())
    assert antes and fase == "reposo" and pantalla != "CoverScreen"
    assert medidas == (86, 43)                                   # 50 filas de alto -> 43 filas, el doble de columnas
    assert [p[0] for p in pedidas][:1] == ["1"] and "2" in [p[0] for p in pedidas]
    assert pedidas[-1][3] == "ascii"


def _res(nombre, artista, album="Disco", pop=50):
    return {"name": nombre, "artists": [{"name": artista}], "album": {"name": album}, "uri": f"spotify:track:{nombre}", "popularity": pop}


def test_pick_best_evita_versiones_no_pedidas():
    items = [_res("Tema Uno - Live", "Banda"), _res("Tema Uno (Remix)", "Banda", pop=90),
             _res("Tema Uno", "Otro Artista"), _res("Tema Uno", "Banda", pop=10)]
    assert sp.pick_best(items, "Tema Uno", "Banda")["popularity"] == 10   # el original, aunque sea menos popular


def test_pick_best_acepta_acentos_y_artistas_en_colaboracion():
    items = [{"name": "Canción Rara", "artists": [{"name": "Dúo Uno"}, {"name": "Banda Dos"}],
              "album": {"name": "X"}, "uri": "u", "popularity": 1}]
    assert sp.pick_best(items, "cancion rara", "Banda Dos") is items[0]
    assert sp.pick_best(items, "Canción Rara", "Nadie") is None
    assert sp.pick_best(items, "Otra", "Banda Dos") is None


def test_pick_best_pide_remix_si_el_titulo_lo_dice():
    items = [_res("Tema Dos (Remix)", "Banda"), _res("Tema Dos", "Banda")]
    assert sp.pick_best(items, "Tema Dos (Remix)", "Banda")["name"] == "Tema Dos (Remix)"
