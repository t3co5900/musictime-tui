"""Letras sincronizadas desde LRCLIB (https://lrclib.net), con caché local."""
import hashlib, json, os, re, time, urllib.error, urllib.parse, urllib.request

CACHE_DIR = os.path.expanduser("~/.cache/musictime/lyrics")
UA = "musictime/0.1 (https://github.com/t3co5900/musictime-tui)"
STAMP = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")
MISS_TTL = 24 * 3600  # un "no encontré" se vuelve a buscar pasado un día
# Agregados de Spotify que LRCLIB no suele tener en el título.
EXTRAS = re.compile(r"\s*[(\[](?:feat\.?|ft\.?|with|con)\s[^)\]]*[)\]]"
                    r"|\s+-\s+.*\b(?:remaster(?:ed)?|live|en vivo|version|versión|edit|mix|mono|stereo"
                    r"|acoustic|ac[uú]stico|from|bonus|demo|deluxe)\b.*$", re.I)


def clean_title(name):
    """'Song - Remastered 2011 (feat. X)' -> 'Song'."""
    return EXTRAS.sub("", name).strip() or name


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
    """None si LRCLIB no lo tiene; los errores de red se propagan para no guardarlos como 'sin letra'."""
    req = urllib.request.Request(f"https://lrclib.net/api/{path}?" + urllib.parse.urlencode(query),
                                 headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _cache_path(track):
    return os.path.join(CACHE_DIR, hashlib.sha1(track["uri"].encode()).hexdigest() + ".json")


def _pick(data):
    if not data or data.get("instrumental"):
        return {"synced": [], "plain": None, "instrumental": bool(data and data.get("instrumental"))}
    return {"synced": parse_lrc(data.get("syncedLyrics")), "plain": data.get("plainLyrics"), "instrumental": False}


def _lookup(track):
    """Prueba de lo más exacto a lo más amplio; devuelve el primer resultado que sirva."""
    artists = [a["name"] for a in track.get("artists") or []] or [""]
    secs = round(track["duration_ms"] / 1000)
    titles = list(dict.fromkeys([track["name"], clean_title(track["name"])]))
    data = _get("get", {"track_name": titles[0], "artist_name": artists[0],
                        "album_name": track["album"]["name"], "duration": secs})
    if data:
        return data
    for title in titles[1:]:
        data = _get("get", {"track_name": title, "artist_name": artists[0], "duration": secs})
        if data:
            return data
    # sin coincidencia exacta: buscar y quedarse con la duración más cercana, prefiriendo la sincronizada
    searches = [{"track_name": t, "artist_name": a} for t in titles for a in artists]
    searches.append({"q": f"{titles[-1]} {artists[0]}"})
    for query in searches:
        found = [x for x in _get("search", query) or [] if abs((x.get("duration") or 0) - secs) <= 3]
        found.sort(key=lambda x: (not x.get("syncedLyrics"), abs(x["duration"] - secs)))
        if found:
            return found[0]
    return None


def fetch(track):
    """Devuelve {'synced': [...], 'plain': str|None, 'instrumental': bool}."""
    path = _cache_path(track)
    try:
        with open(path) as f:
            c = json.load(f)
        # los aciertos valen para siempre; los "no encontré" (o de versiones viejas, sin fecha) vencen
        if c["synced"] or c["plain"] or c["instrumental"] or time.time() - c.get("missed_at", 0) < MISS_TTL:
            return {"synced": [tuple(x) for x in c["synced"]], "plain": c["plain"], "instrumental": c["instrumental"]}
    except (OSError, ValueError, KeyError):
        pass
    out = _pick(_lookup(track))
    cached = out if out["synced"] or out["plain"] or out["instrumental"] else {**out, "missed_at": time.time()}
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "w") as f:
            json.dump(cached, f)
    except OSError:
        pass
    return out
