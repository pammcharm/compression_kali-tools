#!/usr/bin/env bash
set -euo pipefail

MODE="user"
if [[ "${1:-}" == "--system" ]]; then
  MODE="system"
elif [[ "${1:-}" == "--user" || -z "${1:-}" ]]; then
  MODE="user"
else
  echo "Usage: $0 [--user|--system]"
  exit 1
fi

if [[ "$MODE" == "user" ]]; then
  pipx uninstall pamm || true
  rm -f "$HOME/.local/share/bash-completion/completions/pamm" || true
  rm -f "$HOME/.zfunc/_pamm" || true
  echo "User uninstall complete."
  exit 0
fi

# For .deb/self-contained system installs, /usr/bin/pamm and /opt/pamm are owned by dpkg.
# For pip-based system installs, keep this fallback.
sudo python3 -m pip uninstall -y pamm --break-system-packages || true
sudo rm -f /usr/share/bash-completion/completions/pamm || true
sudo rm -f /usr/share/zsh/vendor-completions/_pamm || true
echo "System uninstall complete."
