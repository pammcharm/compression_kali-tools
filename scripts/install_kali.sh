#!/usr/bin/env bash
set -euo pipefail

MODE="user"
DO_APT_UPDATE=0
for arg in "$@"; do
  case "$arg" in
    --system) MODE="system" ;;
    --user) MODE="user" ;;
    --apt-update) DO_APT_UPDATE=1 ;;
    *) echo "Usage: $0 [--user|--system] [--apt-update]"; exit 1 ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

need_cmd() {
  command -v "$1" >/dev/null 2>&1
}

safe_apt_update() {
  if [[ "$DO_APT_UPDATE" != "1" ]]; then
    echo "Skipping apt update by default. Use --apt-update to enable."
    return
  fi
  if ! sudo apt update; then
    echo "Warning: apt update failed (likely third-party repo issue). Continuing with cached indexes."
  fi
}

install_completion_user() {
  local pamm_cmd
  pamm_cmd="$(command -v pamm || true)"
  if [[ -z "$pamm_cmd" ]]; then
    pamm_cmd="$HOME/.local/bin/pamm"
  fi

  mkdir -p "$HOME/.local/share/bash-completion/completions"
  "$pamm_cmd" completion --shell bash > "$HOME/.local/share/bash-completion/completions/pamm" || true

  mkdir -p "$HOME/.zfunc"
  "$pamm_cmd" completion --shell zsh > "$HOME/.zfunc/_pamm" || true

  if ! grep -q 'fpath=(~/.zfunc' "$HOME/.zshrc" 2>/dev/null; then
    {
      echo ''
      echo '# pamm completion'
      echo 'fpath=(~/.zfunc $fpath)'
      echo 'autoload -Uz compinit && compinit'
    } >> "$HOME/.zshrc"
  fi
}

install_completion_system() {
  local pamm_cmd
  pamm_cmd="$(command -v pamm || true)"
  if [[ -z "$pamm_cmd" ]]; then
    return
  fi

  sudo mkdir -p /usr/share/bash-completion/completions
  sudo sh -c '"$1" completion --shell bash > /usr/share/bash-completion/completions/pamm' _ "$pamm_cmd"

  sudo mkdir -p /usr/share/zsh/vendor-completions
  sudo sh -c '"$1" completion --shell zsh > /usr/share/zsh/vendor-completions/_pamm' _ "$pamm_cmd"
}

echo "[1/4] Installing OS dependencies..."
safe_apt_update
sudo apt install -y \
  build-essential \
  cmake \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  zlib1g-dev \
  liblzma-dev \
  bash-completion \
  zsh \
  pipx

if [[ "$MODE" == "user" ]]; then
  echo "[2/4] Installing PAMM for current user via pipx..."
  pipx ensurepath
  pipx install --force "$ROOT_DIR"

  echo "[3/4] Installing shell completion..."
  install_completion_user

  echo "[4/4] Validating installation..."
  if ! need_cmd pamm; then
    echo "pamm is not in PATH yet. Open a new terminal or run: source ~/.zshrc"
  fi
  pamm doctor || true
  echo "Done. Use: pamm --help"
  exit 0
fi

echo "[2/4] Installing PAMM system-wide (all users)..."
sudo python3 -m pip install --upgrade pip --break-system-packages
sudo python3 -m pip install "$ROOT_DIR" --break-system-packages

echo "[3/4] Installing shell completion..."
install_completion_system

echo "[4/4] Validating installation..."
if need_cmd pamm; then
  pamm doctor || true
else
  echo "pamm command not found in PATH after install; check /usr/local/bin"
fi

echo "Done. Use: pamm --help"
