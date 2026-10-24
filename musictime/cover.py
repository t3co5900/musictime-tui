"""Portada del álbum convertida a ASCII en color (con caché local)."""
import hashlib, io, os, urllib.request

from PIL import Image, ImageEnhance

CACHE_DIR = os.path.expanduser("~/.cache/musictime/covers")
RAMP = " .:-=+*#%@"  # de oscuro a claro: más denso = más brillante
UA = "musictime/0.1 (https://github.com/t3co5900/musictime-tui)"


def image_url(album):
    """URL de la portada (la más chica que alcance los 300 px)."""
    imgs = sorted((album or {}).get("images") or [], key=lambda i: i.get("width") or 0)
    if not imgs:
        return None
    return next((i["url"] for i in imgs if (i.get("width") or 0) >= 300), imgs[-1]["url"])


def _load(url):
    path = os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".img")
    try:
        with open(path, "rb") as f:
            return Image.open(io.BytesIO(f.read()))
    except OSError:
        pass
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read()
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(path, "wb") as f:
            f.write(raw)
    except OSError:
        pass
    return Image.open(io.BytesIO(raw))


def _vivo(px):
    """Evita que las zonas oscuras desaparezcan contra el fondo."""
    r, g, b = px
    m = max(r, g, b)
    if 0 < m < 90:
        k = 90 / m
        return int(r * k), int(g * k), int(b * k)
    return r, g, b


def to_grid(img, cols, rows, modo="bloques"):
    """Imagen -> filas de celdas (carácter, color, fondo).

    modo "bloques": medios bloques ▀ (color arriba y fondo abajo): el doble de resolución vertical.
    modo "ascii": un carácter por celda según el brillo. Las celdas son ~2 veces más altas que anchas.
    """
    alto_px = rows * 2 if modo == "bloques" else rows
    im = ImageEnhance.Color(img.convert("RGB").resize((cols, alto_px), Image.LANCZOS)).enhance(1.35)
    px = im.load()
    grid = []
    for y in range(rows):
        row = []
        for x in range(cols):
            if modo == "bloques":
                row.append(("▀", _vivo(px[x, 2 * y]), _vivo(px[x, 2 * y + 1])))
            else:
                r, g, b = px[x, y]
                lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                row.append((RAMP[min(len(RAMP) - 1, int(lum * len(RAMP)))], _vivo((r, g, b)), None))
        grid.append(row)
    return grid


def build(album, cols, rows, modo="bloques"):
    """Descarga (o toma del caché) la portada y devuelve su grilla, o None si no hay."""
    url = image_url(album)
    if not url or cols < 2 or rows < 2:
        return None
    try:
        return to_grid(_load(url), cols, rows, modo)
    except Exception:
        return None
