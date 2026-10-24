"""Letras sincronizadas desde LRCLIB (https://lrclib.net), con caché local."""
import hashlib, json, os, re, urllib.error, urllib.parse, urllib.request

CACHE_DIR = os.path.expanduser("~/.cache/musictime/lyrics")
UA = "musictime/0.1 (https://github.com/t3co5900/musictime-tui)"
STAMP = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_lrc(text):
    """'[mm:ss.xx] línea' -> [(milisegundos, texto)] ordenado por tiempo."""
    lines = []
    for raw in (text or "").splitlines():
        stamps = STAMP.findall(raw)
        body = re.sub(r"\[[^\]]*\]", "", raw).strip()
        for m, s in stamps:
            lines.append((int((int(m) * 60 + float(s)) * 1000), body))
    return sorted(lines, key=lambda x: x[0])


def _get(path, query):
    req = urllib.request.Request(f"https://lrclib.net/api/{path}?" + urllib.parse.urlencode(query),
                                 headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None


def _cache_path(track):
    return os.path.join(CACHE_DIR, hashlib.sha1(track["uri"].encode()).hexdigest() + ".json")


def _pick(data):
    if not data or data.get("instrumental"):
        return {"synced": [], "plain": None, "instrumental": bool(data and data.get("instrumental"))}
    return {"synced": parse_lrc(data.get("syncedLyrics")), "plain": data.get("plainLyrics"), "instrumental": False}


def fetch(track):
    """Devuelve {'synced': [...], 'plain': str|None, 'instrumental': bool}."""
    path = _cache_path(track)
    try:
        with open(path) as f:
            c = json.load(f)
        return {"synced": [tuple(x) for x in c["synced"]], "plain": c["plain"], "instrumental": c["instrumental"]}
    except (OSError, ValueError, KeyError):
        pass
    artist = track["artists"][0]["name"] if track.get("artists") else ""
    secs = round(track["duration_ms"] / 1000)
    data = _get("get", {"track_name": track["name"], "artist_name": artist,
                        "album_name": track["album"]["name"], "duration": secs})
    if not data:  # sin coincidencia exacta: buscar y quedarse con la duración más cercana
        found = _get("search", {"track_name": track["name"], "artist_name": artist}) or []
        found = [x for x in found if abs((x.get("duration") or 0) - secs) <= 3]
        data = next((x for x in found if x.get("syncedLyrics")), found[0] if found else None)
    out = _pick(data)
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w") as f:
            json.dump(out, f)
    except OSError:
        pass
    return out
