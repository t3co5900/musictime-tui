# Registro de cambios

Todos los cambios relevantes de este proyecto se documentan acá. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Agregado
- Tecla `o`: ordena los temas de una playlist o de Guardadas por artista (A-Z, Z-A) o vuelve al orden original. Solo cambia la vista; la playlist en Spotify no se modifica.

## [0.1.2] - 2026-10-24

### Corregido
- Si falta el Client ID (o quedó el texto de ejemplo `PEGA_AQUI_TU_CLIENT_ID`), `musictime` y `musictime login` lo avisan con un mensaje claro y la ruta del archivo, en vez de fallar con `INVALID_CLIENT` en el navegador.
- `musictime` sin configurar ya no pide hacer login: primero avisa que falta el Client ID.
- Un `config.json` con JSON roto da un mensaje comprensible.
- `install.sh` indica el archivo de inicio correcto para el PATH según el shell (`~/.zshrc`, `~/.bashrc` o `~/.bash_profile` en macOS).

### Agregado
- Pruebas automáticas de la configuración (`tests/test_config.py`).

## [0.1.1] - 2026-10-24

### Corregido
- Las playlists con más de 100 temas se veían incompletas: ahora se cargan todos sus temas (por ejemplo, una playlist de unos 500 temas se muestra entera).
- Quien tiene más de 50 playlists ahora las ve todas en la lista.

### Agregado
- Pruebas automáticas de la paginación (`tests/test_spotify.py`).
- Guía de instalación `INSTALLATION.md` y README ampliado (arquitectura, comandos, seguridad).

### Conocido
- Las canciones guardadas (tecla `m`) siguen mostrando los primeros 50 temas.

## [0.1.0] - 2026-10-23

### Agregado
- Primera versión pública: dashboard de terminal para Spotify con playlists, búsqueda, fila, dispositivos, letras sincronizadas y portada a pantalla completa.
- Comandos de línea de comandos y modo scriptable (`taste`, `queue-list`).
- Instaladores para macOS, Linux y Windows, y pruebas automáticas en los tres sistemas.

[0.1.2]: https://github.com/t3co5900/musictime-tui/releases/tag/v0.1.2
[0.1.1]: https://github.com/t3co5900/musictime-tui/releases/tag/v0.1.1
[0.1.0]: https://github.com/t3co5900/musictime-tui/commits/main
