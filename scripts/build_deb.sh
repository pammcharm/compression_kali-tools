#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/dist"
PKG_NAME="pamm"
VERSION="$(python3 - << 'PY'
import tomllib
from pathlib import Path
p=Path('pyproject.toml')
print(tomllib.loads(p.read_text())['project']['version'])
PY
)"
ARCH="$(dpkg --print-architecture)"
PY_MM="$(python3 - << 'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
PY_MM_NEXT="$(python3 - << 'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor + 1}")
PY
)"
PKG_DIR="$OUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}"

rm -rf "$PKG_DIR"
mkdir -p \
  "$PKG_DIR/DEBIAN" \
  "$PKG_DIR/opt/pamm" \
  "$PKG_DIR/usr/bin" \
  "$PKG_DIR/usr/share/doc/pamm"

cp -a "$ROOT_DIR/pamm" "$PKG_DIR/opt/pamm/"
cp -a "$ROOT_DIR/pamm_native.cpython-"*.so "$PKG_DIR/opt/pamm/"
cp "$ROOT_DIR/README.md" "$PKG_DIR/opt/pamm/README.md"
find "$PKG_DIR/opt/pamm/pamm" -type d -name "__pycache__" -prune -exec rm -rf {} +

cat > "$PKG_DIR/DEBIAN/control" << CTRL
Package: pamm
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: PAMM Team
Depends: python3 (>= ${PY_MM}), python3 (<< ${PY_MM_NEXT}), python3-cryptography, zlib1g, liblzma5
Recommends: bash-completion, zsh
Description: PAMM adaptive compressor CLI
 PAMM provides .pamm/.pa compression with native backend and encryption.
 This package is self-contained and does not run apt/pip in maintainer scripts.
CTRL

cat > "$PKG_DIR/usr/bin/pamm" << 'WRAP'
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="/opt/pamm:${PYTHONPATH:-}"
exec /usr/bin/python3 -m pamm.cli "$@"
WRAP
chmod 755 "$PKG_DIR/usr/bin/pamm"

cp "$ROOT_DIR/README.md" "$PKG_DIR/usr/share/doc/pamm/README.md"

mkdir -p "$OUT_DIR"
DEB_PATH="$OUT_DIR/${PKG_NAME}_${VERSION}_${ARCH}.deb"
rm -f "$DEB_PATH"
dpkg-deb --root-owner-group --build "$PKG_DIR" "$DEB_PATH"

echo "Built: $DEB_PATH"
echo "Install with: sudo apt install $DEB_PATH"
echo "Then run: pamm doctor"
