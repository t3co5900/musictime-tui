"""Portada del álbum convertida a ASCII en color (con caché local)."""
import hashlib, io, os, urllib.request

from PIL import Image, ImageEnhance, ImageOps

CACHE_DIR = os.path.expanduser("~/.cache/musictime/covers")
# de oscuro a claro: más denso = más brillante (66 niveles, misma idea que ascii-now-playing)
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
MIN_LUM = 0.12  # en modo ASCII las celdas más oscuras que esto quedan vacías (el fondo hace de sombra)
GAIN = 1.3      # realce de color en modo ASCII: el texto fino se ve más apagado que un bloque lleno
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
    im = img.convert("RGB").resize((cols, alto_px), Image.LANCZOS)
    if modo != "bloques":
        im = ImageOps.autocontrast(im, cutoff=1)  # aprovecha toda la rampa aunque la tapa sea oscura o lavada
    im = ImageEnhance.Color(im).enhance(1.35)
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
                if lum < MIN_LUM:
                    row.append((" ", (0, 0, 0), None))
                    continue
                color = _vivo(tuple(min(255, int(v * GAIN)) for v in (r, g, b)))
                row.append((RAMP[min(len(RAMP) - 1, int(lum * len(RAMP)))], color, None))
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
