#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/install_apt_source.sh https://<user>.github.io/<repo> [key-url]

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <repo-base-url> [gpg-key-url]"
  exit 1
fi

REPO_URL="$1"
KEY_URL="${2:-}"
LIST_FILE="/etc/apt/sources.list.d/pamm.list"
KEYRING_FILE="/usr/share/keyrings/pamm-archive-keyring.gpg"

if [[ -n "$KEY_URL" ]]; then
  curl -fsSL "$KEY_URL" | sudo gpg --dearmor -o "$KEYRING_FILE"
  echo "deb [signed-by=$KEYRING_FILE] $REPO_URL stable main" | sudo tee "$LIST_FILE" >/dev/null
else
  echo "deb [trusted=yes] $REPO_URL stable main" | sudo tee "$LIST_FILE" >/dev/null
  echo "warning: using trusted=yes (unsigned repository)."
fi

sudo apt update
sudo apt install -y pamm
pamm doctor || true
