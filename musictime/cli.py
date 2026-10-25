"""Punto de entrada: `musictime` abre el dashboard; con subcomando actúa y sale."""
import argparse, sys

from . import spotify as sp


def build_parser():
    p = argparse.ArgumentParser(prog="musictime", description="Dashboard de terminal para Spotify.")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("login", help="iniciar sesión con tu app de Spotify")
    sub.add_parser("devices"); sub.add_parser("now"); sub.add_parser("playlists"); sub.add_parser("liked")
    sub.add_parser("pause"); sub.add_parser("resume"); sub.add_parser("next"); sub.add_parser("prev")
    s = sub.add_parser("search"); s.add_argument("query")
    t = sub.add_parser("transfer"); t.add_argument("device")
    qu = sub.add_parser("queue", help="agregar a la fila (texto o URI)")
    qu.add_argument("what"); qu.add_argument("-n", type=int, default=1); qu.add_argument("--device")
    ql = sub.add_parser("queue-list", help='agregar varios a la fila: "Tema - Artista" ...')
    ql.add_argument("items", nargs="*", help='cada uno como "Tema - Artista" (si no hay, se leen de stdin, uno por línea)')
    ql.add_argument("--play-first", action="store_true", help="el primero suena ya y el resto va a la fila")
    ql.add_argument("--dry-run", action="store_true", help="solo verificar coincidencias, sin tocar la fila")
    sub.add_parser("taste", help="resumen de tu gusto (guardadas y playlists propias)")
    pl = sub.add_parser("play"); pl.add_argument("what", help="URI spotify:track:... o texto a buscar")
    pl.add_argument("--device")
    v = sub.add_parser("volume"); v.add_argument("percent", type=int)
    return p


def run(a):
    if a.cmd == "devices":
        for d in sp.devices():
            print(("* " if d["is_active"] else "  ") + f'{d["name"]} ({d["type"]}) vol {d["volume_percent"]}')
    elif a.cmd == "search":
        for x in sp.search(a.query, 5):
            print(x["uri"], "|", x["name"], "-", sp.artists(x), "|", x["album"]["name"])
    elif a.cmd == "play":
        track = {"uri": a.what} if a.what.startswith("spotify:") else sp.search(a.what, 1)[0]
        sp.play_track(track, device=a.device); print("Reproduciendo", track.get("name", track["uri"]))
    elif a.cmd == "queue":
        items = [{"uri": a.what, "name": a.what, "artists": []}] if a.what.startswith("spotify:") else sp.search(a.what, a.n)
        for x in items:
            sp.add_to_queue(x["uri"], a.device); print("En fila:", x["name"], "-", sp.artists(x))
    elif a.cmd == "taste":
        t = sp.taste()
        print("Artistas más frecuentes en tus guardadas:", ", ".join(f"{n} ({c})" for n, c in t["guardadas"]))
        print("Artistas más frecuentes en tus playlists:", ", ".join(f"{n} ({c})" for n, c in t["playlists"]))
        print("Últimas guardadas:", "; ".join(t["recientes"]))
    elif a.cmd == "queue-list":
        pedidos = a.items or [l.strip() for l in sys.stdin if l.strip()]
        faltan = 0
        for n, pedido in enumerate(pedidos):
            if " - " not in pedido:
                print(f"✗ formato inválido (usá 'Tema - Artista'): {pedido}"); faltan += 1; continue
            titulo, artista = pedido.rsplit(" - ", 1)
            x = sp.find_track(titulo.strip(), artista.strip())
            if not x:
                print(f"✗ no encontré: {pedido}"); faltan += 1; continue
            if a.dry_run:
                print(f"✓ {x['name']} - {sp.artists(x)} ({x['album']['name']})"); continue
            if a.play_first and n == 0:
                sp.play_track(x); print(f"▶ suena: {x['name']} - {sp.artists(x)}")
            else:
                sp.add_to_queue(x["uri"]); print(f"✓ en fila: {x['name']} - {sp.artists(x)}")
        if faltan:
            print(f"({faltan} de {len(pedidos)} sin agregar)")
    elif a.cmd == "playlists":
        for pl in sp.playlists():
            print(pl["uri"], "|", pl["name"])
    elif a.cmd == "liked":
        for x in sp.liked_tracks(20):
            print(x["uri"], "|", x["name"], "-", sp.artists(x))
    elif a.cmd == "transfer":
        sp.transfer(a.device, play=False); print("Transferido")
    elif a.cmd == "now":
        d = sp.playback()
        if not d or not d.get("item"):
            return print("Nada sonando")
        i = d["item"]
        print("▶" if d["is_playing"] else "⏸", i["name"], "-", sp.artists(i), "|", i["album"]["name"], "|",
              sp.fmt_ms(d["progress_ms"]), "/", sp.fmt_ms(i["duration_ms"]), "|", d["device"]["name"])
    elif a.cmd in ("pause", "resume", "next", "prev"):
        {"pause": sp.pause, "resume": sp.play, "next": sp.next_track, "prev": sp.prev_track}[a.cmd](); print("OK")
    elif a.cmd == "volume":
        sp.set_volume(a.percent); print("OK")


def main():
    a = build_parser().parse_args()
    try:
        if a.cmd == "login":
            sp.login(); return print("Login guardado.")
        if a.cmd is None:
            sp.client_id()  # avisa primero si falta configurar, antes que pedir el login
            if not sp.is_logged_in():
                sys.exit("Primero iniciá sesión: musictime login")
            from .tui import MusicTime
            return MusicTime().run()
        run(a)
    except sp.SpotifyError as e:
        sys.exit(f"Error: {e}")
