# Registro de cambios

Todos los cambios relevantes de este proyecto se documentan acá. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

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

[0.1.1]: https://github.com/t3co5900/musictime-tui/releases/tag/v0.1.1
[0.1.0]: https://github.com/t3co5900/musictime-tui/commits/main
