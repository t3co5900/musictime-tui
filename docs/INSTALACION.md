# Guía de instalación paso a paso

Esta guía está pensada para alguien que **nunca usó la terminal ni Git**. Cada paso explica qué se hace y para qué. Seguila en orden:

1. [Qué necesitás](#1-qué-necesitás)
2. [Crear tu app de Spotify y sacar el Client ID](#2-crear-tu-app-de-spotify-y-sacar-el-client-id) (igual para todos los sistemas)
3. Instalar `musictime` en tu sistema: [Windows](#3a-windows) · [Ubuntu / Debian](#3b-ubuntu-y-debian) · [Otras distribuciones de Linux](#3c-otras-distribuciones-de-linux) · [macOS](#3d-macos)
4. [Primer uso](#4-primer-uso)
5. [Problemas comunes](#5-problemas-comunes) · [Actualizar](#actualizar) · [Desinstalar](#desinstalar)

---

## 1. Qué necesitás

| Cosa | Para qué sirve |
|---|---|
| **Cuenta de Spotify Premium** | Spotify solo deja que otros programas controlen la reproducción si tenés Premium. |
| **La app de Spotify** (en la PC, el celular o el navegador) | `musictime` **no reproduce música por sí mismo**: manda órdenes a Spotify, y es Spotify el que suena. |
| **Git** | Programa que descarga el código desde GitHub y permite actualizarlo después. |
| **Python 3.10 o más nuevo** | `musictime` está escrito en Python; necesitás tenerlo para que pueda ejecutarse. |
| **Una terminal con colores** | La ventana de texto donde vas a escribir los comandos. Se explica abajo cómo abrirla. |

> **¿Qué es la terminal?** Es una ventana donde escribís órdenes en vez de hacer clic. Escribís un comando, apretás **Enter** y el sistema lo ejecuta. En esta guía los comandos aparecen en cajas grises: copiás el texto, lo pegás en la terminal y apretás Enter. Nunca hace falta escribir el símbolo `$` ni `>` del inicio, si aparece.

---

## 2. Crear tu app de Spotify y sacar el Client ID

**¿Por qué hace falta?** Para que un programa pueda hablar con tu cuenta, Spotify exige que esté registrado como "aplicación". No hay una clave compartida: **cada persona crea la suya, gratis**, y así nadie usa tu cuenta ni vos la de otros. El resultado es un código llamado **Client ID** (un identificador público, no es una contraseña).

1. Abrí https://developer.spotify.com/dashboard en el navegador e **iniciá sesión con tu cuenta de Spotify**. Si es la primera vez, te pide aceptar los términos para desarrolladores.
2. Hacé clic en **Create app** (crear aplicación).
3. Completá el formulario:
   - **App name:** el nombre que quieras, por ejemplo `musictime`.
   - **App description:** cualquier frase, por ejemplo `Control de Spotify desde la terminal`.
   - **Website:** podés dejarlo vacío.
   - **Redirect URIs:** escribí **exactamente** `http://127.0.0.1:8989/login` y hacé clic en **Add**. Tiene que quedar en la lista debajo del campo.
     - *¿Qué es esto?* Cuando iniciás sesión, Spotify te devuelve a esa dirección para entregarle el permiso a `musictime`. La dirección apunta a **tu propia computadora** (`127.0.0.1` siempre significa "esta máquina"), no a internet.
     - Tiene que ser `127.0.0.1`, **no** `localhost`, y el número `8989` y el `/login` también tienen que estar tal cual.
   - **Which API/SDKs are you planning to use?:** marcá **Web API**.
4. Aceptá los términos (casilla al final) y hacé clic en **Save**.
5. Entrá a la app que acabás de crear y abrí **Settings** (configuración). Ahí vas a ver el **Client ID**: un texto largo de letras y números. **Copialo**, lo vas a pegar más adelante.
   - No hace falta el *Client Secret*. No lo compartas ni lo uses acá.

> Si más adelante el login dice `INVALID_CLIENT` o `redirect_uri`, casi siempre es porque el Client ID está mal copiado o porque la Redirect URI no coincide exactamente. Volvé a esta sección y revisalas.

---

## 3a. Windows

Probado a mano en Windows con estos mismos pasos. Si algo falla, mirá [Problemas comunes](#5-problemas-comunes).

### Paso 1: abrir una terminal
- **Windows 11:** apretá la tecla Windows, escribí **Terminal** y abrí *Terminal* (o *Windows Terminal*).
- **Windows 10:** instalá **Windows Terminal** gratis desde la Microsoft Store, o abrí **PowerShell** desde el menú Inicio.

Usá **PowerShell**, no el "Símbolo del sistema" (CMD) clásico: el CMD viejo no muestra bien los colores. En *Windows Terminal* el perfil por defecto ya es PowerShell.

### Paso 2: instalar Git y Python
Pegá estos comandos, uno por vez:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.13 -e
```

*¿Qué hace?* `winget` es el instalador de programas que trae Windows. Estos comandos descargan e instalan Git y Python. Si te pregunta algo (aceptar términos), escribí `S` o `Y` y Enter.

Si `winget` no existe en tu Windows, instalalos a mano:
- Git: https://git-scm.com/download/win (dejá todo en las opciones por defecto).
- Python: https://www.python.org/downloads/ . **En la primera pantalla del instalador marcá la casilla "Add python.exe to PATH"**; sin eso, la terminal no encuentra Python.

### Paso 3: cerrar y volver a abrir la terminal
Esto es obligatorio. La terminal que ya estaba abierta no se entera de lo que acabás de instalar. Verificá que funcionó:

```powershell
git --version
python --version
```

Cada uno tiene que mostrar un número de versión (por ejemplo `git version 2.x` y `Python 3.13.x`). Si `python` te lleva a la tienda de Microsoft, mirá [Problemas comunes](#5-problemas-comunes).

### Paso 4: descargar musictime
```powershell
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
```

*¿Qué hace?* `git clone` descarga una copia del código en una carpeta llamada `musictime-tui`, dentro de la carpeta donde estés (normalmente tu carpeta de usuario). `cd musictime-tui` entra a esa carpeta.

> **No borres ni muevas esa carpeta después de instalar.** El programa se ejecuta desde ahí.

### Paso 5: instalar
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

*¿Qué hace?* Corre el script de instalación, que: crea un entorno privado de Python solo para `musictime` (así no ensucia el resto del sistema), instala sus dependencias, crea el comando `musictime` y crea el archivo de configuración. La parte `-ExecutionPolicy Bypass` es porque Windows, por seguridad, bloquea scripts por defecto: esto lo permite **solo para esta ejecución**, sin cambiar la configuración de tu sistema.

Cuando termine, **cerrá la terminal y abrí una nueva**, para que reconozca el comando `musictime`.

### Paso 6: pegar tu Client ID
```powershell
notepad $env:USERPROFILE\.config\musictime\config.json
```

Se abre el Bloc de notas. Reemplazá todo el contenido por esto, con **tu** Client ID entre comillas, y guardá (Ctrl+S):

```json
{"client_id": "pegá-acá-tu-client-id"}
```

Seguí en [Primer uso](#4-primer-uso).

---

## 3b. Ubuntu y Debian

Requiere **Ubuntu 22.04 o más nuevo** (o Debian 12 o más nuevo), que ya traen Python 3.10 o superior. En versiones más viejas, Python es muy antiguo.

### Paso 1: abrir una terminal
Apretá **Ctrl + Alt + T**, o buscá "Terminal" en el menú de aplicaciones.

### Paso 2: instalar Git y Python
```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

*¿Qué hace?* `sudo` ejecuta el comando con permisos de administrador (te pide tu contraseña; al escribirla no se ve nada, es normal). `apt update` refresca la lista de programas disponibles y `apt install` instala Git y Python. `python3-venv` es la pieza que permite crear el entorno privado de `musictime`; sin ella la instalación falla.

Verificá:
```bash
git --version
python3 --version
```
`python3 --version` tiene que mostrar 3.10 o más.

### Paso 3: descargar musictime
```bash
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
```
*¿Qué hace?* Descarga el código en la carpeta `musictime-tui` y entra a ella. **No la borres después**: el programa se ejecuta desde ahí.

### Paso 4: instalar
```bash
./install.sh
```
*¿Qué hace?* Crea un entorno privado de Python, instala lo necesario, deja el comando `musictime` en `~/.local/bin` y crea el archivo de configuración `~/.config/musictime/config.json`.

Si el instalador avisa que `~/.local/bin` no está en tu PATH, o si después `musictime` dice "command not found", ejecutá esto y **abrí una terminal nueva**:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```
*¿Qué es el PATH?* La lista de carpetas donde el sistema busca los comandos. Esto agrega la carpeta donde quedó `musictime`.

### Paso 5: pegar tu Client ID
```bash
nano ~/.config/musictime/config.json
```
Se abre un editor de texto en la terminal. Borrá el contenido y escribí esto, con **tu** Client ID:
```json
{"client_id": "pegá-acá-tu-client-id"}
```
Para guardar: **Ctrl+O**, Enter. Para salir: **Ctrl+X**.

### Paso 6: tener Spotify abierto
Instalá la app de Spotify (por ejemplo `sudo snap install spotify`, o desde el centro de software) o usá el reproductor web en https://open.spotify.com . Iniciá sesión y reproducí cualquier tema una vez.

Seguí en [Primer uso](#4-primer-uso).

---

## 3c. Otras distribuciones de Linux

Los pasos son los mismos que en Ubuntu; solo cambia el comando para instalar Git y Python:

| Distribución | Comando |
|---|---|
| Fedora | `sudo dnf install git python3` |
| Arch / Manjaro | `sudo pacman -S git python` |
| openSUSE | `sudo zypper install git python3` |

Después seguí con el **Paso 3 de Ubuntu** (descargar) en adelante. Necesitás Python 3.10 o más nuevo.

---

## 3d. macOS

### Paso 1: abrir la terminal
Apretá **Cmd + Espacio**, escribí **Terminal** y Enter.

### Paso 2: instalar Git y Python
La forma más simple es con **Homebrew**, el instalador de programas de macOS. Si no lo tenés, instalalo desde https://brew.sh (copiá el comando que muestra la página). Después:

```bash
brew install git python
```

(Alternativa: `xcode-select --install` instala Git, y Python se baja de https://www.python.org/downloads/ .)

### Paso 3: descargar, instalar y configurar
```bash
git clone https://github.com/t3co5900/musictime-tui.git
cd musictime-tui
./install.sh
nano ~/.config/musictime/config.json
```
Dentro de `nano`, dejá el contenido así, con **tu** Client ID, y guardá con **Ctrl+O**, Enter, **Ctrl+X**:
```json
{"client_id": "pegá-acá-tu-client-id"}
```
Si `musictime` no se encuentra después, mirá el aviso del instalador sobre el PATH (en macOS se agrega a `~/.zshrc` en lugar de `~/.bashrc`).

---

## 4. Primer uso

Los mismos pasos en todos los sistemas, ya con el Client ID guardado:

1. **Iniciar sesión (una sola vez por computadora):**
   ```
   musictime login
   ```
   Se abre el navegador con una pantalla de Spotify. Hacé clic en **Aceptar**. Si dice "Listo, volvé a la terminal", funcionó. Se guarda un permiso en tu carpeta de usuario (en `.config/musictime`); no se sube a ningún lado. Si el navegador no se abre solo, copiá el enlace que aparece en la terminal y pegalo en el navegador.
2. **Tener Spotify abierto** en algún dispositivo y reproducir un tema una vez. Así Spotify marca ese dispositivo como "activo", que es al que `musictime` le manda las órdenes.
3. **Abrir el dashboard:**
   ```
   musictime
   ```
   Arranca mostrando tus playlists. Las teclas principales: **flechas** para moverte, **Enter** para abrir o reproducir, **espacio** para pausa, **/** para buscar, **y** para ver la letra, **c** para ver la portada grande, **q** para salir. La tabla completa está en el [README](../README.md#uso).

---

## 5. Problemas comunes

| Qué ves | Qué significa y cómo se arregla |
|---|---|
| Windows: *"la ejecución de scripts está deshabilitada en este sistema"* | Windows bloquea scripts por defecto. Usá el comando con `-ExecutionPolicy Bypass` del Paso 5. |
| Windows: `python` abre la Microsoft Store o dice *"Python was not found"* | Windows trae un atajo falso. Ir a **Configuración > Aplicaciones > Configuración avanzada de aplicaciones > Alias de ejecución de aplicaciones** y desactivar los de `python.exe` y `python3.exe`. Si instalaste Python a mano, reinstalalo marcando **"Add python.exe to PATH"**. Después abrí una terminal nueva. |
| `musictime` → *"no se reconoce como comando"* / *"command not found"* | La terminal no conoce todavía el comando. Abrí una terminal **nueva**. En Linux/macOS, agregá `~/.local/bin` al PATH (ver el Paso 4 de Ubuntu). |
| Ubuntu: *"ensurepip is not available"* o falla al crear el entorno | Falta `python3-venv`: `sudo apt install python3-venv` y volvé a correr `./install.sh`. |
| *"Falta client_id"* | El archivo `config.json` no tiene tu Client ID, o quedó con el texto de ejemplo. Revisá el Paso de "pegar tu Client ID". |
| El navegador muestra `INVALID_CLIENT` o un error de *redirect URI* | El Client ID está mal copiado, o la Redirect URI de tu app de Spotify no es exactamente `http://127.0.0.1:8989/login`. Revisá la [sección 2](#2-crear-tu-app-de-spotify-y-sacar-el-client-id). |
| El puerto 8989 está ocupado al hacer login | Otro programa lo usa. Cerralo y reintentá `musictime login`. |
| *"No active device"* / el dashboard no controla nada | Abrí Spotify, reproducí un tema una vez y reintentá. |
| Los colores se ven raros o la portada es un manchón | La terminal no soporta colores reales. Usá Windows Terminal (Windows), GNOME Terminal / Konsole (Linux) o la app Terminal / iTerm2 (macOS). |
| Error 403 al abrir una playlist ajena | Es una restricción de Spotify: esas playlists no se pueden listar. Aparecen como `▶ solo reproducir`; Enter las reproduce completas. |
| La letra no aparece | No todos los temas están en el servicio de letras. El dashboard lo avisa. |

Si nada de esto ayuda, abrí un *issue* en el repositorio y pegá el mensaje de error completo.

---

## Actualizar
Entrá a la carpeta `musictime-tui` en la terminal y corré:

```
git pull
```
y después el mismo instalador de antes (`./install.sh` o el comando de PowerShell).

## Desinstalar
1. Borrá la carpeta `musictime-tui`.
2. Borrá los datos del programa:
   - **Linux / macOS:** `rm -rf ~/.local/share/musictime ~/.local/bin/musictime ~/.config/musictime ~/.cache/musictime`
   - **Windows (PowerShell):**
     ```powershell
     Remove-Item -Recurse -Force "$env:LOCALAPPDATA\musictime", "$env:USERPROFILE\.config\musictime"
     ```
3. Opcional: en https://www.spotify.com/account/apps/ quitá el permiso de tu app, y en el dashboard de desarrolladores borrá la app que creaste.
