"""Cliente mínimo de la Web API de Spotify (solo librería estándar)."""
import base64, hashlib, http.server, json, os, secrets, time
import urllib.error, urllib.parse, urllib.request, webbrowser

CONFIG_DIR = os.path.expanduser("~/.config/musictime")
CONFIG = os.path.join(CONFIG_DIR, "config.json")
TOKEN = os.path.join(CONFIG_DIR, "token.json")
REDIRECT = "http://127.0.0.1:8989/login"
SCOPES = ("user-read-playback-state user-modify-playback-state user-read-currently-playing "
          "playlist-read-private playlist-read-collaborative user-library-read user-library-modify")
API = "https://api.spotify.com/v1"


class SpotifyError(Exception):
    pass


def _write_private(path, data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)


def _read(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def client_id():
    cfg = _read(CONFIG) or {}
    if not cfg.get("client_id"):
        raise SpotifyError(f'Falta client_id en {CONFIG} ({{"client_id": "..."}})')
    return cfg["client_id"]


def is_logged_in():
    return _read(TOKEN) is not None


def _token_request(params):
    req = urllib.request.Request("https://accounts.spotify.com/api/token",
                                 data=urllib.parse.urlencode(params).encode())
    try:
        with urllib.request.urlopen(req) as r:
            tok = json.load(r)
    except urllib.error.HTTPError as e:
        raise SpotifyError(f"Spotify rechazó el login ({e.code}): {e.read().decode()[:200]}")
    tok["expires_at"] = time.time() + tok["expires_in"] - 30
    return tok


def login(show=print):
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(12)
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id(), "response_type": "code", "redirect_uri": REDIRECT,
        "scope": SCOPES, "state": state, "code_challenge_method": "S256", "code_challenge": challenge})
    got = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Listo, volvé a la terminal.".encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 8989), Handler)
    show("Abrí este link y aceptá:\n" + url)
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        srv.handle_request()
    srv.server_close()
    if got.get("state") != state or "code" not in got:
        raise SpotifyError(f"Login fallido: {got.get('error', 'estado inválido')}")
    _write_private(TOKEN, _token_request({
        "grant_type": "authorization_code", "code": got["code"], "redirect_uri": REDIRECT,
        "client_id": client_id(), "code_verifier": verifier}))


def access_token():
    tok = _read(TOKEN)
    if not tok:
        raise SpotifyError("No hay login. Corré: musictime login")
    if time.time() >= tok["expires_at"]:
        new = _token_request({"grant_type": "refresh_token", "refresh_token": tok["refresh_token"],
                              "client_id": client_id()})
        new.setdefault("refresh_token", tok["refresh_token"])
        _write_private(TOKEN, new)
        tok = new
    return tok["access_token"]


def api(method, path, body=None, query=None):
    url = API + path + ("?" + urllib.parse.urlencode(query) if query else "")
    req = urllib.request.Request(url, method=method, headers={"Authorization": "Bearer " + access_token()},
                                 data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        try:
            msg = json.loads(detail)["error"]["message"]
        except (ValueError, KeyError, TypeError):
            msg = detail[:200]
        wait = f" (reintentar en {e.headers.get('Retry-After')}s)" if e.code == 429 else ""
        raise SpotifyError(f"{msg}{wait} [HTTP {e.code}]")
    except urllib.error.URLError as e:
        raise SpotifyError(f"Sin conexión: {e.reason}")
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None  # algunos endpoints (p. ej. queue) responden sin JSON


def devices():
    return api("GET", "/me/player/devices")["devices"]


def device_id(name):
    devs = devices()
    for d in devs:
        if d["name"].lower() == name.lower():
            return d["id"]
    raise SpotifyError("Dispositivo no encontrado. Disponibles: " + ", ".join(d["name"] for d in devs))


SEARCH_PAGE = 10  # Spotify rechaza (HTTP 400) límites mayores a 10 por página


def search(query, limit=10):
    items = []
    while len(items) < limit:
        page = api("GET", "/search", query={"q": query, "type": "track", "limit": min(SEARCH_PAGE, limit - len(items)),
                                            "offset": len(items)})["tracks"]["items"]
        items += page
        if len(page) < SEARCH_PAGE:
            break
    return items


def playback():
    return api("GET", "/me/player")


def queue():
    return api("GET", "/me/player/queue") or {}


def play(uri=None, device=None):
    q = {"device_id": device_id(device)} if device else None
    api("PUT", "/me/player/play", {"uris": [uri]} if uri else None, q)


def play_track(track, context_uri=None, device=None):
    """Reproduce un tema dentro de su contexto (playlist o álbum).

    La app de escritorio no carga temas sueltos enviados con `uris`: hay que darle un contexto.
    """
    context = context_uri or track.get("album", {}).get("uri")
    if not context:
        return play(track["uri"], device)
    q = {"device_id": device_id(device)} if device else None
    api("PUT", "/me/player/play", {"context_uri": context, "offset": {"uri": track["uri"]}}, q)


_ME = {}


def me_id():
    if "id" not in _ME:
        _ME["id"] = api("GET", "/me")["id"]
    return _ME["id"]


def play_context(context_uri, device=None):
    """Reproduce una playlist/álbum completo, sin listar sus temas."""
    q = {"device_id": device_id(device)} if device else None
    api("PUT", "/me/player/play", {"context_uri": context_uri}, q)


def can_browse(playlist):
    """Spotify solo deja leer los temas de playlists propias o colaborativas (HTTP 403 en el resto)."""
    return playlist["owner"]["id"] == me_id() or bool(playlist.get("collaborative"))


def playlists():
    out = []
    while True:
        data = api("GET", "/me/playlists", query={"limit": 50, "offset": len(out)})
        out += data["items"]
        if not data["items"] or not data.get("next"):
            return out


def playlist_tracks(playlist_id, max_items=None):
    """Temas de una playlist, paginando de a 100 hasta el final (o hasta `max_items` si se indica)."""
    out, offset, path = [], 0, f"/playlists/{playlist_id}/tracks"
    while True:
        query = {"limit": 100, "offset": offset}
        try:
            data = api("GET", path, query=query)
        except SpotifyError:
            if offset:
                raise
            path = f"/playlists/{playlist_id}/items"
            data = api("GET", path, query=query)
        for it in data["items"]:
            t = it.get("track") or it.get("item")
            if t and t.get("uri", "").startswith("spotify:track:"):
                out.append(t)
        offset += len(data["items"])
        if not data["items"] or not data.get("next") or (max_items and len(out) >= max_items):
            return out[:max_items] if max_items else out


def liked_tracks(limit=50):
    out = []
    while len(out) < limit:
        page = api("GET", "/me/tracks", query={"limit": min(50, limit - len(out)), "offset": len(out)})["items"]
        out += [it["track"] for it in page if it.get("track")]
        if len(page) < 50:
            break
    return out


def taste(limit=250):
    """Resumen del gusto: artistas más frecuentes en tus guardadas y playlists propias, y últimas guardadas."""
    from collections import Counter
    liked = liked_tracks(limit)
    guardadas = Counter(t["artists"][0]["name"] for t in liked if t.get("artists"))
    en_listas = Counter()
    me = me_id()
    for pl in [p for p in playlists() if p["owner"]["id"] == me][:6]:
        try:
            en_listas.update(t["artists"][0]["name"] for t in playlist_tracks(pl["id"], 60) if t.get("artists"))
        except SpotifyError:
            pass
    return {"guardadas": guardadas.most_common(20), "playlists": en_listas.most_common(15),
            "recientes": [f"{t['name']} - {t['artists'][0]['name']}" for t in liked[:15]]}


# --- buscar un tema exacto por "Tema - Artista" ---
_VERSIONES = ("live", "en vivo", "remix", "karaoke", "cover", "tribute", "instrumental", "acoustic", "sped up",
              "slowed", "reverb", "nightcore", "8d", "version")


def _norm(texto):
    import re, unicodedata
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def pick_best(items, titulo, artista):
    """Elige el resultado que coincide en título y artista, sin versiones no pedidas (live, remix...)."""
    t, a = _norm(titulo), _norm(artista)
    mejor, mejor_puntaje = None, None
    for x in items:
        nombre = _norm(x["name"])
        if not (nombre == t or nombre.startswith(t + " ")):
            continue
        if not any(a in _norm(art["name"]) or _norm(art["name"]) in a for art in x.get("artists", [])):
            continue
        extra = f" {nombre[len(t):]} {_norm(x.get('album', {}).get('name', ''))} "
        no_pedidas = sum(1 for v in _VERSIONES if f" {v} " in extra and f" {v} " not in f" {t} ")
        puntaje = (-no_pedidas, nombre == t, x.get("popularity", 0))
        if mejor_puntaje is None or puntaje > mejor_puntaje:
            mejor, mejor_puntaje = x, puntaje
    return mejor


def find_track(titulo, artista):
    for q in (f'track:"{titulo}" artist:"{artista}"', f"{titulo} {artista}"):
        hallado = pick_best(search(q, 10), titulo, artista)
        if hallado:
            return hallado
    return None


def pause():
    api("PUT", "/me/player/pause")


def next_track():
    api("POST", "/me/player/next")


def prev_track():
    api("POST", "/me/player/previous")


def set_volume(percent):
    api("PUT", "/me/player/volume", query={"volume_percent": max(0, min(100, percent))})


def set_shuffle(on):
    api("PUT", "/me/player/shuffle", query={"state": "true" if on else "false"})


def set_repeat(mode):
    api("PUT", "/me/player/repeat", query={"state": mode})


def transfer(device, play=True):
    api("PUT", "/me/player", {"device_ids": [device_id(device)], "play": play})


def transfer_id(dev_id, play=True):
    api("PUT", "/me/player", {"device_ids": [dev_id], "play": play})


def add_to_queue(uri, device=None):
    q = {"uri": uri}
    if device:
        q["device_id"] = device_id(device)
    api("POST", "/me/player/queue", query=q)


def fmt_ms(ms):
    return f"{ms // 60000}:{ms // 1000 % 60:02d}"


def artists(track):
    return ", ".join(a["name"] for a in track.get("artists", []))
