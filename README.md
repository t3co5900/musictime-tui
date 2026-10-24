<h1 align="center">musictime</h1>

<p align="center">
  Dashboard de terminal para controlar Spotify: playlists, búsqueda, fila, letras sincronizadas y portada a pantalla completa.
</p>

<p align="center">
  <a href="https://github.com/t3co5900/musictime-tui/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/t3co5900/musictime-tui/actions/workflows/tests.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="Plataformas" src="https://img.shields.io/badge/macOS%20%7C%20Windows%20%7C%20Linux-lightgrey">
  <a href="LICENSE"><img alt="Licencia MIT" src="https://img.shields.io/badge/licencia-MIT-green"></a>
</p>

> **English:** a terminal dashboard (built on [Textual](https://textual.textualize.io)) that remote-controls Spotify through the official Web API: playlists, search, queue, synced lyrics and a full-screen cover. It needs Spotify Premium and your own free Spotify developer app; no credentials ship with the repo. Setup guide in [INSTALLATION.md](INSTALLATION.md) (Spanish). Not affiliated with Spotify.

---

## Índice
1. [Qué es](#qué-es)
2. [Características](#características)
3. [Cómo funciona](#cómo-funciona)
4. [Instalación rápida](#instalación-rápida)
5. [Configuración](#configuración-una-sola-vez)
6. [Uso](#uso)
7. [Seguridad y privacidad](#seguridad-y-privacidad)
8. [Límites de Spotify](#límites-de-spotify-que-conviene-conocer)
9. [Compatibilidad](#compatibilidad)
10. [Estructura del proyecto](#estructura-del-proyecto)
11. [Desarrollo](#desarrollo)
12. [Licencia y aviso](#licencia-y-aviso)

## Qué es

`musictime` permite manejar Spotify sin sacar las manos de la terminal. **No reproduce audio por sí mismo**: envía órdenes a la Web API oficial de Spotify y el sonido sale por la app de Spotify que ya tengas abierta (PC, celular, navegador, parlante o cualquier dispositivo Spotify Connect).

Tiene dos modos de uso:
- **Dashboard interactivo** (`musictime`): una interfaz de terminal con listas navegables, barra de progreso, letras y portada.
- **Línea de comandos** (`musictime now`, `play`, `queue-list`…): comandos cortos y scriptables para automatizar o integrar con otras herramientas.

## Características

- **Navegación completa:** tus playlists, tus canciones guardadas, la fila de reproducción y los dispositivos disponibles.
- **Búsqueda** de temas con paginación automática.
- **Control de reproducción:** play/pausa, siguiente/anterior, volumen, shuffle, repeat y cambio de dispositivo.
- **Letras sincronizadas** a pantalla completa: la línea que suena brilla en dorado y las demás se apagan con la distancia.
- **Portada a pantalla completa** en medios bloques (más detalle) o ASCII, con animación al cambiar de tema.
- **Modo scriptable:** `taste` resume tus artistas más frecuentes y `queue-list` arma la fila a partir de textos `"Tema - Artista"`, descartando versiones en vivo, remix o karaoke no pedidas.
- **Sin dependencias pesadas:** el cliente de Spotify usa solo la librería estándar de Python; el resto es Textual y Pillow.
- **Multiplataforma:** instaladores para macOS, Linux y Windows, con pruebas automáticas en los tres.

## Cómo funciona

```
┌──────────────┐   Web API (HTTPS)   ┌──────────────┐   audio   ┌──────────────────┐
│  musictime   │ ──────────────────▶ │   Spotify    │ ────────▶ │ App / dispositivo│
│ (tu terminal)│ ◀────────────────── │   servidores │           │ Spotify Connect  │
└──────┬───────┘   estado, listas    └──────────────┘           └──────────────────┘
       │
       ├── LRCLIB (letras)         → caché en ~/.cache/musictime/lyrics
       └── CDN de Spotify (portada)→ caché en ~/.cache/musictime/covers
```

**Autenticación.** Cada persona registra su propia app gratuita en el [panel de desarrolladores de Spotify](https://developer.spotify.com/dashboard) y usa su **Client ID** (un identificador público, no una contraseña). `musictime login` aplica el flujo OAuth 2.0 *Authorization Code con PKCE*: abre el navegador, recibe la respuesta en un servidor local temporal (`http://127.0.0.1:8989/login`) y guarda el token. Los tokens se renuevan solos. Solo se piden los permisos necesarios: leer y modificar la reproducción, leer playlists y leer/modificar tus canciones guardadas.

**Dashboard.** Está hecho con [Textual](https://textual.textualize.io). Consulta el estado de Spotify cada 3 segundos y anima la barra de progreso cada 0,5 s. Todas las llamadas de red corren en hilos de trabajo, así que la interfaz no se congela.

**Letras y portada.** Las letras se piden a [LRCLIB](https://lrclib.net) (servicio público, sin cuenta) con búsqueda por duración si no hay coincidencia exacta. Las portadas se descargan del CDN de Spotify y se convierten a celdas de terminal con Pillow. Ambas quedan en caché local.

## Instalación rápida

Requisitos: **Spotify Premium**, **Python 3.10+**, **Git** y una terminal con colores reales (*truecolor*).

> ¿Primera vez con la terminal, Git o Python? Seguí la **[guía de instalación paso a paso](INSTALLATION.md)**: explica todo, incluida la creación de tu app de Spotify, para Windows, Ubuntu/Linux y macOS.

**macOS / Linux**
```bash
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
./install.sh
```

**Windows (PowerShell, recomendado Windows Terminal)**
```powershell
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

**Cualquier sistema, con pipx**
```bash
pipx install git+https://github.com/t3co5900/musictime-tui.git
```

El instalador crea un entorno virtual propio, instala las dependencias, deja el comando `musictime` disponible y genera el archivo de configuración. Para actualizar: `git pull` y volver a correr el instalador.

## Configuración (una sola vez)

1. Entrá a https://developer.spotify.com/dashboard y creá una app.
2. En *Redirect URIs* agregá exactamente `http://127.0.0.1:8989/login` (con `127.0.0.1`, no `localhost`) y marcá **Web API**.
3. Copiá el **Client ID** (el Client Secret no hace falta) y pegalo en el archivo de configuración:
   - macOS / Linux: `~/.config/musictime/config.json`
   - Windows: `%USERPROFILE%\.config\musictime\config.json`

   ```json
   {"client_id": "tu-client-id"}
   ```
4. Corré `musictime login` y aceptá en el navegador.

Detalle con capturas de cada campo en la [guía de instalación](INSTALLATION.md#2-crear-tu-app-de-spotify-y-sacar-el-client-id).

## Uso

Con Spotify abierto en algún dispositivo, corré `musictime`. Arranca mostrando tus playlists.

### Atajos del dashboard

| Tecla | Acción |
|---|---|
| `espacio` | play / pausa |
| `n` / `p` | siguiente / anterior |
| `+` / `-` | volumen |
| `s` / `r` | shuffle / repeat |
| `/` | ir a la barra de búsqueda (Enter busca, Esc vuelve a la lista) |
| `Enter` | abrir playlist / reproducir tema |
| `a` | agregar el tema seleccionado a la fila |
| `l` | tus playlists |
| `m` | tus canciones guardadas |
| `f` | la fila |
| `d` | dispositivos (Enter pasa la música ahí) |
| `y` | letra sincronizada a pantalla completa |
| `c` | portada a pantalla completa (`a` cambia entre medios bloques y ASCII) |
| `q` | salir |

### Comandos

| Comando | Qué hace |
|---|---|
| `musictime login` | inicia sesión con tu app de Spotify |
| `musictime now` | muestra el tema en reproducción, progreso y dispositivo |
| `musictime play "tema artista"` | busca y reproduce (acepta también una URI `spotify:track:…`) |
| `musictime queue "tema artista" [-n 3]` | agrega a la fila los primeros *n* resultados |
| `musictime pause` · `resume` · `next` · `prev` | control básico |
| `musictime volume 30` | volumen de 0 a 100 |
| `musictime devices` · `transfer "nombre"` | lista dispositivos y pasa la reproducción a uno |
| `musictime playlists` · `liked` · `search "texto"` | consultas |
| `musictime taste` | tus artistas más frecuentes y últimas guardadas |
| `musictime queue-list "Tema - Artista" …` | busca cada tema exacto y lo agrega a la fila |

`queue-list` acepta `--dry-run` (solo verifica las coincidencias), `--play-first` (el primero suena ya y el resto va a la fila) y lee de la entrada estándar si no se le pasan temas, uno por línea.

## Seguridad y privacidad

- **El repositorio no contiene claves.** Cada usuario usa su propio Client ID; no se necesita el Client Secret.
- **Login con PKCE** y verificación del parámetro `state`; el servidor local solo escucha en `127.0.0.1` y se cierra al terminar.
- **El token** se guarda en `~/.config/musictime/token.json` (en macOS/Linux con permisos `600`) y nunca sale de tu computadora.
- **Servicios externos que se contactan:** Spotify (API y CDN de portadas) y LRCLIB (letras). No hay telemetría ni analítica.
- Para revocar el acceso: https://www.spotify.com/account/apps/

## Límites de Spotify que conviene conocer

- Los temas de **playlists de otras personas** no se pueden listar (la API devuelve 403): aparecen como `▶ solo reproducir`, y Enter las reproduce completas.
- La búsqueda devuelve de a 10 resultados por página; el dashboard junta las páginas necesarias.
- La API de Spotify no deja vaciar ni reordenar la fila.
- Si el dashboard dice que no hay dispositivo activo, abrí Spotify y poné cualquier tema una vez.
- La API solo permite controlar la reproducción con cuentas **Premium**.

## Compatibilidad

| Sistema | Estado |
|---|---|
| **macOS** | Probado a mano. |
| **Windows 10/11** | Probado a mano con `install.ps1` y la [guía de instalación](INSTALLATION.md); se ve bien en Windows Terminal. |
| **Linux (Ubuntu/Debian y otras)** | Las pruebas automáticas pasan, pero **todavía nadie lo probó a mano en una máquina real**. Si lo probás, contanos cómo te fue en un *issue*. |

Las pruebas automáticas corren en Linux, macOS y Windows con Python 3.10 y 3.13 mediante GitHub Actions. La apariencia depende de que tu terminal soporte colores reales.

## Estructura del proyecto

```
musictime-tui/
├── musictime/
│   ├── cli.py        # punto de entrada y subcomandos
│   ├── spotify.py    # cliente de la Web API: OAuth PKCE, reproducción, búsqueda, gusto
│   ├── tui.py        # dashboard (Textual): lista, barra de estado, letras y portada
│   ├── lyrics.py     # letras sincronizadas desde LRCLIB, con caché
│   └── cover.py      # portada → celdas de terminal con Pillow, con caché
├── tests/            # pruebas con una API de Spotify simulada
├── install.sh        # instalador macOS / Linux
├── install.ps1       # instalador Windows
├── INSTALLATION.md   # guía paso a paso
└── .github/workflows # CI en Linux, macOS y Windows
```

## Desarrollo

```bash
pip install -e . pytest
python -m pytest tests
```
Las pruebas usan una API de Spotify simulada: no necesitan cuenta ni red.

## Licencia y aviso

MIT (ver [LICENSE](LICENSE)). Proyecto independiente, **no afiliado a Spotify**. Spotify es una marca de Spotify AB. Usá tu propia app de desarrollador y respetá sus [términos para desarrolladores](https://developer.spotify.com/terms).
