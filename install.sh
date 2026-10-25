#!/usr/bin/env bash
# Instala musictime en un entorno propio y crea el comando en ~/.local/bin.
# Para actualizar: git pull && ./install.sh
set -euo pipefail
cd "$(dirname "$0")"

VENV="$HOME/.local/share/musictime/venv"
BIN="$HOME/.local/bin"

python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -e .

mkdir -p "$BIN"
ln -sf "$VENV/bin/musictime" "$BIN/musictime"

mkdir -p "$HOME/.config/musictime"
if [ ! -f "$HOME/.config/musictime/config.json" ]; then
  echo '{"client_id": "PEGA_AQUI_TU_CLIENT_ID"}' > "$HOME/.config/musictime/config.json"
  echo "Editá ~/.config/musictime/config.json con tu Client ID de Spotify."
fi

case ":$PATH:" in
  *":$BIN:"*) ;;
  *)
    case "$(basename "${SHELL:-}")" in
      zsh)  RC="~/.zshrc" ;;
      bash) if [ "$(uname)" = "Darwin" ]; then RC="~/.bash_profile"; else RC="~/.bashrc"; fi ;;
      *)    RC="" ;;
    esac
    if [ -n "$RC" ]; then
      echo "Agregá $BIN al PATH y abrí una terminal nueva: echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> $RC"
    else
      echo "Agregá $BIN al PATH de tu shell (archivo de inicio, por ejemplo ~/.profile): export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi ;;
esac
echo "Listo. Primera vez: musictime login. Después: musictime"
