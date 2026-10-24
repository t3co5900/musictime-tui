# musictime

Dashboard de terminal para controlar Spotify: playlists, búsqueda, fila, letras sincronizadas y portada a pantalla completa. El audio suena en tu app de Spotify (o en cualquier dispositivo Spotify Connect); `musictime` solo manda las órdenes por la Web API.

> **English:** a terminal dashboard (Textual) that remote-controls Spotify through the Web API: playlists, search, queue, synced lyrics and a full-screen cover. Needs Spotify Premium and your own free Spotify developer app. Setup steps below (in Spanish). Not affiliated with Spotify.

## Requisitos
- **Spotify Premium** (la API de Spotify solo permite controlar la reproducción con Premium).
- **Python 3.10 o más nuevo** y una terminal con colores reales (truecolor).
- La app de Spotify abierta en algún dispositivo (PC, celular, parlante…): `musictime` no reproduce audio por sí mismo.

## Instalación

**macOS / Linux**
```bash
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
./install.sh
```
En Debian/Ubuntu puede hacer falta `sudo apt install python3-venv`. Si `~/.local/bin` no está en tu `PATH`, el instalador te dice cómo agregarlo.

**Windows (PowerShell, recomendado Windows Terminal)**
```powershell
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
.\install.ps1
```
Abrí una terminal nueva para que reconozca el comando `musictime`. Si PowerShell bloquea el script: `powershell -ExecutionPolicy Bypass -File .\install.ps1`.

**Cualquier sistema, con pipx**
```bash
pipx install git+https://github.com/t3co5900/musictime-tui.git
```

Para actualizar: `git pull` y volver a correr el instalador.

## Configuración (una sola vez)
Cada persona usa **su propia app de Spotify** (gratis); el repo no trae ninguna clave.
1. Entrá a https://developer.spotify.com/dashboard y creá una app.
2. En *Redirect URIs* agregá exactamente `http://127.0.0.1:8989/login` (con `127.0.0.1`, no `localhost`) y marcá **Web API**.
3. Copiá el **Client ID** (el Client Secret no hace falta) y pegalo en el archivo de configuración:
   - macOS / Linux: `~/.config/musictime/config.json`
   - Windows: `%USERPROFILE%\.config\musictime\config.json`

   ```json
   {"client_id": "tu-client-id"}
   ```
4. Corré `musictime login` y aceptá en el navegador. El token queda en la misma carpeta (en macOS/Linux con permisos 600).

## Uso
Con Spotify abierto, corré `musictime`. Arranca mostrando tus playlists.

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

También funciona sin interfaz:
`musictime now`, `play "tema artista"`, `queue "tema artista"`, `pause`, `resume`, `next`, `prev`, `volume 30`, `devices`, `playlists`, `liked`, `search "texto"`.
Para scripts: `musictime taste` (tus artistas más frecuentes) y `musictime queue-list "Tema - Artista" ...` (busca cada tema, descarta versiones en vivo/remix no pedidas y lo agrega a la fila; `--dry-run` solo verifica).

## Letras y portada
- **Letras:** se piden a [LRCLIB](https://lrclib.net) (servicio público, sin cuenta) y se guardan en `~/.cache/musictime/lyrics/`. La línea que suena brilla en dorado y las demás se apagan con la distancia. No todos los temas tienen letra allí.
- **Portada:** `c` la muestra lo más grande que entre en la terminal, en medios bloques (más detalle) o ASCII. Al cambiar de tema la portada vieja se deshace y la nueva sube desde abajo. Se guardan en `~/.cache/musictime/covers/`.

## Límites de Spotify que conviene conocer
- Los temas de **playlists de otras personas** no se pueden listar (la API devuelve 403): aparecen como `▶ solo reproducir`, y Enter las reproduce completas.
- La búsqueda devuelve de a 10 resultados por página; el dashboard junta las páginas necesarias.
- La API de Spotify no deja vaciar ni reordenar la fila.
- Si el dashboard dice que no hay dispositivo activo, abrí Spotify y poné cualquier tema una vez.

## Compatibilidad
Desarrollado y probado a mano en **macOS**. El código usa solo Python estándar, [Textual](https://textual.textualize.io) y [Pillow](https://python-pillow.org), que funcionan en Linux y Windows; las pruebas automáticas corren en Linux, macOS y Windows con GitHub Actions (mirá la pestaña *Actions*). Lo que no se probó a mano en Linux ni Windows es el aspecto real en cada terminal y los instaladores en máquinas reales: si algo falla, abrí un *issue* con el mensaje de error.

## Desarrollo
```bash
pip install -e . pytest
python -m pytest tests
```
Las pruebas usan una API de Spotify simulada: no necesitan cuenta ni red.

## Licencia y aviso
MIT (ver `LICENSE`). Proyecto independiente, **no afiliado a Spotify**. Spotify es una marca de Spotify AB. Usá tu propia app de desarrollador y respetá sus [términos para desarrolladores](https://developer.spotify.com/terms).
