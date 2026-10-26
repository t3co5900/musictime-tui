"""Dashboard de terminal: la música suena en la app de Spotify, acá se manda todo."""
import time

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from rich.text import Text
from textual.containers import Vertical
from textual.theme import Theme
from textual.widgets import DataTable, Footer, Header, Input, Static

import math
from bisect import bisect_right

from textual.screen import Screen

from . import cover as cv
from . import lyrics as ly
from . import spotify as sp

POLL_SECONDS = 3

# Paleta: negro y grises de base, azul pastel como color principal, dorado de acento.
AZUL = "#a8c7fa"
DORADO = "#e6c76f"
BLANCO = "#f4f5f7"
GRIS = "#8a93a3"
GRIS_OSCURO = "#3a4150"

TEMA = Theme(
    name="musictime",
    primary=AZUL,
    secondary="#7fa6e8",
    accent=DORADO,
    warning=DORADO,
    error="#f28b82",
    success="#9fd8b5",
    foreground=BLANCO,
    background="#0d1016",
    surface="#141923",
    panel="#1a202c",
    dark=True,
)


FONDO = (13, 16, 22)  # mismo tono que el fondo del tema


def _mezcla(c, k):
    """Acerca el color c al fondo: k=1 deja c intacto, k=0 lo funde con el fondo."""
    return "rgb(%d,%d,%d)" % tuple(int(f + (v - f) * k) for v, f in zip(c, FONDO))


def _ruido(x, y):
    """Número fijo en [0, 1) por celda: decide en qué orden se deshace la portada."""
    return ((x * 73856093) ^ (y * 19349663)) % 1000 / 1000


class CoverView(Static):
    """Portada ASCII en color: la vieja se disuelve y la nueva sube desde abajo."""

    SALIDA = 0.8   # segundos que tarda en deshacerse
    ENTRADA = 1.1  # segundos que tarda en subir la nueva

    def __init__(self, **kw):
        super().__init__("", **kw)
        self.grid = None
        self.siguiente = None
        self.hay_siguiente = False
        self.fase, self.t = "reposo", 0.0
        self.sucio = True

    def comenzar_salida(self):
        if self.fase == "reposo" and self.grid:
            self.fase, self.t = "salida", 0.0

    def mostrar(self, grid):
        """Cambia la portada con animación (la actual se deshace y entra la nueva)."""
        self.siguiente, self.hay_siguiente = grid, True
        if self.fase == "reposo" and self.grid:
            self.fase, self.t = "salida", 0.0
        elif self.fase in ("reposo", "vacio"):
            self._entrar()

    def fijar(self, grid):
        """Cambia la portada sin animar (por ejemplo, al redimensionar)."""
        self.grid, self.siguiente, self.hay_siguiente = grid, None, False
        self.fase, self.t, self.sucio = "reposo", 0.0, True

    def _entrar(self):
        self.grid, self.siguiente, self.hay_siguiente = self.siguiente, None, False
        self.fase, self.t = ("entrada" if self.grid else "reposo"), 0.0

    def avanzar(self, dt):
        if self.fase == "reposo" and not self.sucio:
            return
        self.t += dt
        if self.fase == "salida" and self.t >= self.SALIDA:
            self.grid, self.fase, self.t = None, "vacio", 0.0
            if self.hay_siguiente:
                self._entrar()
        elif self.fase == "entrada" and self.t >= self.ENTRADA:
            self.fase, self.t = "reposo", 0.0
        self.sucio = self.fase != "reposo"
        if self.is_attached:  # sin app montada (p. ej. en pruebas) solo avanza el estado
            self.update(self.dibujar())

    def dibujar(self):
        g = self.grid
        out = Text(no_wrap=True)
        if not g:
            return out
        alto = len(g)
        frente = (self.t / self.ENTRADA) * (alto + 3) if self.fase == "entrada" else None
        p = min(1.0, self.t / self.SALIDA) if self.fase == "salida" else 0.0
        for y, fila in enumerate(g):
            if y:
                out.append("\n")
            for x, (ch, c, *resto) in enumerate(fila):
                fondo = resto[0] if resto else None
                if self.fase == "salida":
                    k = None if _ruido(x, y) < p else 1 - 0.7 * p
                elif frente is not None:
                    d = frente - (alto - 1 - y)  # cuánto pasó el frente por esta fila (de abajo hacia arriba)
                    k = None if d <= 0 else min(1.0, d / 3)
                else:
                    k = 1.0
                if k is None:
                    out.append(" ")
                else:
                    estilo = _mezcla(c, k) + (f" on {_mezcla(fondo, k)}" if fondo else "")
                    out.append(ch, style=estilo)
        return out


class MusicTime(App):
    TITLE = "musictime"
    CSS = """
    Screen { background: $background; }
    Header { background: $surface; color: $accent; text-style: bold; }
    #now { height: 7; border: round $accent; background: $surface; padding: 0 2; margin: 1 1 0 1; }
    #search { margin: 1 1 0 1; border: round $primary; background: $surface; color: $foreground; }
    #search:focus { border: round $accent; }
    #modo { height: 1; color: $primary; text-style: italic; padding: 0 2; margin-top: 1; }
    DataTable { height: 1fr; margin: 0 1; background: $background; border: round #2a3140; }
    DataTable > .datatable--header { background: $surface; color: $accent; text-style: bold; }
    DataTable > .datatable--cursor { background: $primary; color: #0d1016; text-style: bold; }
    DataTable > .datatable--even-row { background: #10141c; }
    Footer { background: $surface; }
    Footer .footer-key--key { color: $accent; background: $surface; text-style: bold; }
    Footer .footer-key--description { color: $text-muted; }
    """
    BINDINGS = [
        Binding("space", "toggle", "Play"),
        Binding("n", "next", "Sig."),
        Binding("p", "prev", "Ant."),
        Binding("plus,equals", "vol(5)", "Vol+"),
        Binding("minus", "vol(-5)", "Vol-"),
        Binding("s", "shuffle", "Shuf"),
        Binding("r", "repeat", "Rep"),
        Binding("slash", "search", "Buscar"),
        Binding("c", "cover", "Portada"),
        Binding("y", "lyrics", "Letra"),
        Binding("l", "show_playlists", "Listas"),
        Binding("m", "show_liked", "Guardadas"),
        Binding("f", "show_queue", "Fila"),
        Binding("d", "show_devices", "Equipos"),
        Binding("a", "enqueue", "+Fila"),
        Binding("o", "sort", "Orden"),
        Binding("q", "quit", "Salir"),
    ]

    def __init__(self):
        super().__init__()
        self.state = None
        self.polled_at = 0.0
        self.mode = "results"
        self.rows = {}
        self.tracks = {}
        self.context_uri = None
        self.playlist_uris = {}
        self.playlist_browsable = {}
        self.source_tracks = []  # temas de la lista abierta, en el orden de Spotify
        self.sort_i = 0

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("Conectando con Spotify…", id="now")
            yield Input(placeholder="🔍  Buscar cualquier tema o artista…  (tecla / para escribir · Enter busca · Esc vuelve a la lista)", id="search")
            yield Static("", id="modo")
            yield DataTable(cursor_type="row", zebra_stripes=True)
        yield Footer()

    def on_mount(self):
        self.register_theme(TEMA)
        self.theme = "musictime"
        self.query_one(DataTable).focus()  # el foco arranca en la lista; / salta a la búsqueda
        self.refresh_state()
        self.set_interval(POLL_SECONDS, self.refresh_state)
        self.set_interval(0.5, self.draw_now)
        self.action_show_playlists()

    # --- estado ---
    @work(thread=True, exclusive=True, group="poll")
    def refresh_state(self):
        try:
            state = sp.playback()
        except sp.SpotifyError as e:
            self.call_from_thread(self.notify, str(e), severity="error")
            return
        self.state, self.polled_at = state, time.monotonic()
        self.call_from_thread(self.draw_now)


    def position_ms(self):
        s = self.state
        if not s or not s.get("item"):
            return 0
        pos = s["progress_ms"] + (int((time.monotonic() - self.polled_at) * 1000) if s["is_playing"] else 0)
        return min(pos, s["item"]["duration_ms"])

    def draw_now(self):
        w = self.query_one("#now", Static)
        s = self.state
        if not s or not s.get("item"):
            w.update(f"[{GRIS}]Nada sonando.[/]\n[{GRIS}]Abrí la app de Spotify, buscá un tema con[/] [b {DORADO}]/[/] [{GRIS}]y dale Enter.[/]")
            return
        i, dev = s["item"], s["device"]
        pos, dur = self.position_ms(), i["duration_ms"]
        ancho = max(10, w.size.width - 12)  # el panel comparte la fila con la portada: medir el panel, no la pantalla
        lleno = int(ancho * pos / dur) if dur else 0
        barra = f"[{AZUL}]{'━' * lleno}[/][{GRIS_OSCURO}]{'━' * (ancho - lleno)}[/]"
        ico = f"[{DORADO}]▶[/]" if s["is_playing"] else f"[{GRIS}]⏸[/]"
        on = lambda v: f"[{DORADO}]{v}[/]"
        extra = (f"[{GRIS}]shuffle[/] {on('on') if s.get('shuffle_state') else f'[{GRIS}]off[/]'}  "
                 f"[{GRIS}]repeat[/] {on(s.get('repeat_state', 'off')) if s.get('repeat_state', 'off') != 'off' else f'[{GRIS}]off[/]'}  "
                 f"[{GRIS}]vol[/] [{BLANCO}]{dev.get('volume_percent', '?')}%[/]  [{GRIS}]en[/] [{AZUL}]{dev['name']}[/]")
        w.update(f"{ico} [b {BLANCO}]{i['name']}[/]\n[{AZUL}]{sp.artists(i)}[/] [{GRIS}]— {i['album']['name']}[/]\n"
                 f"[{DORADO}]{sp.fmt_ms(pos)}[/] {barra} [{GRIS}]{sp.fmt_ms(dur)}[/]\n{extra}")

    # --- acciones: se ejecutan en hilos para no congelar la interfaz ---
    @work(thread=True)
    def cmd(self, fn, *args):
        try:
            fn(*args)
        except sp.SpotifyError as e:
            self.call_from_thread(self.notify, str(e), severity="error")
        self.call_from_thread(self.refresh_state)

    def action_toggle(self):
        playing = self.state and self.state.get("is_playing")
        self.cmd(sp.pause if playing else sp.play)

    def action_next(self): self.cmd(sp.next_track)
    def action_prev(self): self.cmd(sp.prev_track)

    def action_vol(self, delta: int):
        cur = (self.state or {}).get("device", {}).get("volume_percent", 50)
        self.cmd(sp.set_volume, cur + delta)

    def action_shuffle(self): self.cmd(sp.set_shuffle, not (self.state or {}).get("shuffle_state"))

    def action_repeat(self):
        orden = ["off", "context", "track"]
        cur = (self.state or {}).get("repeat_state", "off")
        self.cmd(sp.set_repeat, orden[(orden.index(cur) + 1) % 3])

    # --- tabla: resultados, fila y dispositivos ---
    def fill(self, mode, titulo, cols, rows):
        t = self.query_one(DataTable)
        t.clear(columns=True)
        t.add_columns(*cols)
        self.mode, self.rows = mode, {}
        for key, cells in rows:
            t.add_row(*cells, key=key)
            self.rows[key] = cells
        self.query_one("#modo", Static).update(titulo)
        t.focus()

    def track_rows(self, tracks, mode):
        # La clave lleva la posición: una playlist puede repetir el mismo tema.
        keyed = [(f"{n}:{x['uri']}", x) for n, x in enumerate(tracks)]
        self.tracks = dict(keyed)
        return [(k, (x["name"], sp.artists(x), x["album"]["name"], sp.fmt_ms(x["duration_ms"]))) for k, x in keyed]

    def sorted_tracks(self):
        _, reverse = SORTS[self.sort_i]
        if reverse is None:
            return list(self.source_tracks)
        return sorted(self.source_tracks, key=lambda x: sp.artists(x).casefold(), reverse=reverse)

    def sort_title(self, mode):
        base = ("Playlist (Enter reproduce · l vuelve a tus playlists" if mode == "playlist_tracks"
                else "Mis canciones (Enter reproduce")
        return f"{base} · o cambia el orden) — orden: {SORTS[self.sort_i][0]}"

    def action_sort(self):
        if self.mode not in ("playlist_tracks", "liked"):
            return self.notify("El orden por artista funciona dentro de una playlist o en Guardadas.")
        self.sort_i = (self.sort_i + 1) % len(SORTS)
        self.fill(self.mode, self.sort_title(self.mode), ("Tema", "Artista", "Álbum", "Dur"),
                  self.track_rows(self.sorted_tracks(), self.mode))

    @work(thread=True, exclusive=True, group="table")
    def load(self, mode, arg=None):
        cols = ("Tema", "Artista", "Álbum", "Dur")
        try:
            if mode == "queue":
                q = sp.queue()
                args = ("queue", "Fila (/ para buscar)", cols, self.track_rows(q.get("queue", [])[:30], mode))
            elif mode == "playlists":
                pls = sp.playlists()
                self.playlist_uris = {p["id"]: p["uri"] for p in pls}
                self.playlist_browsable = {p["id"]: sp.can_browse(p) for p in pls}
                rows = [(p["id"], (p["name"], str((p.get("tracks") or p.get("items") or {}).get("total", "")),
                                   "tuya" if p["owner"]["id"] == sp.me_id() else (p["owner"].get("display_name") or p["owner"]["id"]),
                                   "" if self.playlist_browsable[p["id"]] else "▶ solo reproducir")) for p in pls]
                args = ("playlists", "Tus playlists (Enter abre · las de otras personas solo se pueden reproducir completas)",
                        ("Playlist", "Temas", "De", ""), rows)
            elif mode == "playlist_tracks":
                self.context_uri = self.playlist_uris.get(arg)
                self.source_tracks, self.sort_i = sp.playlist_tracks(arg), 0
                args = ("playlist_tracks", self.sort_title(mode), cols, self.track_rows(self.sorted_tracks(), mode))
            elif mode == "liked":
                self.source_tracks, self.sort_i = sp.liked_tracks(), 0
                args = ("liked", self.sort_title(mode), cols, self.track_rows(self.sorted_tracks(), mode))
            else:
                rows = [(d["id"], (("● " if d["is_active"] else "") + d["name"], d["type"], f"{d['volume_percent']}%"))
                        for d in sp.devices()]
                args = ("devices", "Dispositivos (Enter para pasar la música ahí)", ("Nombre", "Tipo", "Vol"), rows)
        except sp.SpotifyError as e:
            self.call_from_thread(self.notify, str(e), severity="error")
            return
        self.call_from_thread(self.fill, *args)

    def action_cover(self):
        self.push_screen(CoverScreen())

    def action_lyrics(self):
        self.push_screen(LyricsScreen())

    def action_show_queue(self): self.load("queue")
    def action_show_playlists(self): self.load("playlists")
    def action_show_liked(self): self.load("liked")
    def action_show_devices(self): self.load("devices")

    def action_search(self):
        self.query_one("#search", Input).focus()

    def on_key(self, event):
        if event.key == "escape":
            self.query_one("#search", Input).value = ""
            self.query_one(DataTable).focus()

    @work(thread=True, exclusive=True, group="table")
    def do_search(self, text):
        try:
            items = sp.search(text, 15)
        except sp.SpotifyError as e:
            self.call_from_thread(self.notify, str(e), severity="error")
            return
        rows = self.track_rows(items, "results")
        self.call_from_thread(self.fill, "results", f"Resultados de “{text}” (Enter reproduce · a agrega a la fila)",
                              ("Tema", "Artista", "Álbum", "Dur"), rows)

    def on_input_submitted(self, event: Input.Submitted):
        if event.value.strip():
            self.do_search(event.value.strip())

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        key = event.row_key.value
        if self.mode == "playlists":
            if self.playlist_browsable.get(key, True):
                self.load("playlist_tracks", key)
            else:
                self.notify("Spotify no deja ver los temas de playlists ajenas: la reproduzco completa.")
                self.cmd(sp.play_context, self.playlist_uris[key])
        elif self.mode in ("results", "liked", "queue"):
            self.cmd(sp.play_track, self.tracks[key])
        elif self.mode == "playlist_tracks":
            self.cmd(sp.play_track, self.tracks[key], self.context_uri)
        elif self.mode == "devices":
            self.cmd(sp.transfer_id, key)

    def action_enqueue(self):
        if not self.tracks or self.mode in ("playlists", "devices"):
            return self.notify("Elegí un tema (con / buscás) y usá 'a' para agregarlo a la fila.")
        t = self.query_one(DataTable)
        if t.row_count:
            key = t.coordinate_to_cell_key(t.cursor_coordinate).row_key.value
            self.cmd(sp.add_to_queue, self.tracks[key]["uri"])
            self.notify("Agregado a la fila")


# Órdenes de la lista de temas: (nombre, reverse); None conserva el orden de Spotify.
SORTS = [("original", None), ("artista A-Z", False), ("artista Z-A", True)]

# Gradiente de la letra según la distancia a la línea actual.
HALO = [None, AZUL, "#7f9fd0", "#5b7099", GRIS_OSCURO]
LEAD_MS = 250  # adelanto para compensar la latencia de la API


class LyricsScreen(Screen):
    """Letra a pantalla completa: la línea que suena brilla y el resto se apaga."""

    DEFAULT_CSS = """
    LyricsScreen { background: #090b10; align: center middle; }
    #l-head { dock: top; height: 3; content-align: center middle; text-align: center; color: $text-muted; }
    #l-body { width: 100%; height: 1fr; content-align: center middle; text-align: center; padding: 0 4; }
    #l-foot { dock: bottom; height: 1; text-align: center; color: $text-muted; }
    """
    BINDINGS = [Binding("escape,y,q", "app.pop_screen", "Volver")]

    def __init__(self):
        super().__init__()
        self.uri = None
        self.data = None  # None: cargando

    def compose(self) -> ComposeResult:
        yield Static("", id="l-head")
        yield Static("", id="l-body")
        yield Static(f"[{DORADO}]Esc[/] volver", id="l-foot")

    def on_mount(self):
        self.set_interval(0.1, self.tick)

    @work(thread=True, exclusive=True)
    def cargar(self, track):
        try:
            data = ly.fetch(track)
        except Exception:
            data = {"synced": [], "plain": None, "instrumental": False}
        self.app.call_from_thread(setattr, self, "data", data)

    def tick(self):
        st = self.app.state
        item = st.get("item") if st else None
        body = self.query_one("#l-body", Static)
        if not item:
            return body.update(f"[{GRIS}]Nada sonando[/]")
        if item["uri"] != self.uri:
            self.uri, self.data = item["uri"], None
            self.cargar(item)
            self.query_one("#l-head", Static).update(
                f"[b {BLANCO}]{item['name']}[/]\n[{AZUL}]{sp.artists(item)}[/]")
        if self.data is None:
            return body.update(f"[{GRIS}]Buscando la letra…[/]")
        if self.data["instrumental"]:
            return body.update(f"[{DORADO}]♪ Instrumental ♪[/]")
        lines = self.data["synced"]
        if not lines:
            plain = self.data["plain"]
            msg = f"[{GRIS}]Letra sin sincronizar[/]\n\n" + "\n".join(plain.splitlines()[:self.size.height - 8]) if plain \
                else f"[{GRIS}]No encontré la letra de este tema[/]"
            return body.update(msg)
        pos = self.app.position_ms() + LEAD_MS
        cur = max(0, bisect_right([t for t, _ in lines], pos) - 1)
        if pos < lines[0][0]:
            cur = -1
        filas = max(5, self.size.height - 8)
        mitad = filas // 2
        pulso = (math.sin(time.monotonic() * 3) + 1) / 2  # 0..1: brillo que respira
        brillo = "#%02x%02x%02x" % (int(230 + 25 * pulso), int(199 + 45 * pulso), int(111 + 100 * pulso))
        out = []
        for k in range(cur - mitad, cur + mitad + 1):
            if k < 0 or k >= len(lines):
                out.append("")
                continue
            texto = lines[k][1] or "♪"
            d = abs(k - cur)
            if d == 0:
                out.append(f"[b {brillo}]✦  {texto}  ✦[/]")
            else:
                out.append(f"[{HALO[min(d, len(HALO) - 1)]}]{texto}[/]")
        body.update("\n".join(out))


class CoverScreen(Screen):
    """Portada a pantalla completa, lo más grande posible, con la misma animación de cambio de tema."""

    DEFAULT_CSS = """
    CoverScreen { background: #0d1016; align: center middle; }
    #c-cover { width: 100%; height: 10; content-align: center top; }
    #c-info { width: 100%; height: 3; content-align: center middle; text-align: center; margin-top: 1; }
    #c-foot { dock: bottom; height: 1; text-align: center; color: $text-muted; }
    """
    BINDINGS = [Binding("escape,c,q", "app.pop_screen", "Volver"), Binding("a", "estilo", "Estilo")]

    def __init__(self):
        super().__init__()
        self.url = None
        self.album = None
        self.modo = "bloques"
        self.medidas = (0, 0)

    def compose(self) -> ComposeResult:
        yield CoverView(id="c-cover")
        yield Static("", id="c-info")
        yield Static(f"[{DORADO}]Esc[/] volver   [{DORADO}]a[/] cambiar estilo (bloques / ASCII)", id="c-foot")

    def on_mount(self):
        self.ajustar()
        self.set_interval(1 / 20, self.paso)

    def ajustar(self):
        """Tamaño máximo cuadrado: las celdas son ~2 veces más altas que anchas."""
        ancho, alto = self.size
        filas = max(4, alto - 7)
        cols = filas * 2
        if cols > ancho - 4:
            cols = max(8, (ancho - 4) // 2 * 2)
            filas = cols // 2
        vista = self.query_one("#c-cover", CoverView)
        vista.styles.height = filas  # el ancho es 100% y la portada se centra con content-align
        if (cols, filas) != self.medidas:
            self.medidas = (cols, filas)
            if self.album:
                self.cargar(self.album, animar=False)

    def on_resize(self, event):
        self.ajustar()

    @work(thread=True, exclusive=True, group="cover")
    def cargar(self, album, animar=True):
        cols, filas = self.medidas
        grid = cv.build(album, cols, filas, self.modo) if album else None
        vista = self.query_one("#c-cover", CoverView)
        self.app.call_from_thread(vista.mostrar if animar else vista.fijar, grid)

    def action_estilo(self):
        self.modo = "ascii" if self.modo == "bloques" else "bloques"
        if self.album:
            self.cargar(self.album, animar=False)

    def paso(self):
        vista = self.query_one("#c-cover", CoverView)
        vista.avanzar(1 / 20)
        st = self.app.state
        item = st.get("item") if st else None
        album = item["album"] if item else None
        url = cv.image_url(album) if album else None
        if url != self.url:
            self.url, self.album = url, album
            vista.comenzar_salida()
            self.cargar(album)
            self.query_one("#c-info", Static).update(
                f"[b {BLANCO}]{item['name']}[/]\n[{AZUL}]{sp.artists(item)}[/] [{GRIS}]— {album['name']}[/]" if item
                else f"[{GRIS}]Nada sonando[/]")
