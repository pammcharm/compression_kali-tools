#!/usr/bin/env bash
set -euo pipefail

# Build a Debian APT repository tree from local .deb files in ./dist
# Optional signing with GPG key if available.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
REPO_DIR="$ROOT_DIR/aptrepo"
CODENAME="stable"
COMPONENT="main"
ARCH="$(dpkg --print-architecture)"

if ! command -v dpkg-scanpackages >/dev/null 2>&1; then
  echo "error: dpkg-scanpackages not found. Install: sudo apt install dpkg-dev"
  exit 1
fi

mkdir -p "$REPO_DIR/pool/$COMPONENT" "$REPO_DIR/dists/$CODENAME/$COMPONENT/binary-$ARCH"

# Copy all pamm .deb packages into pool.
shopt -s nullglob
DEBS=("$DIST_DIR"/pamm_*_*.deb)
if [[ ${#DEBS[@]} -eq 0 ]]; then
  echo "error: no pamm .deb found in $DIST_DIR. Run ./scripts/build_deb.sh first."
  exit 1
fi
cp -f "${DEBS[@]}" "$REPO_DIR/pool/$COMPONENT/"

pushd "$REPO_DIR" >/dev/null

dpkg-scanpackages --multiversion "pool/$COMPONENT" /dev/null > "dists/$CODENAME/$COMPONENT/binary-$ARCH/Packages"
gzip -9c "dists/$CODENAME/$COMPONENT/binary-$ARCH/Packages" > "dists/$CODENAME/$COMPONENT/binary-$ARCH/Packages.gz"

cat > "dists/$CODENAME/Release" << REL
Origin: PAMM
Label: PAMM
Suite: $CODENAME
Codename: $CODENAME
Architectures: $ARCH
Components: $COMPONENT
Description: PAMM APT repository
Date: $(LC_ALL=C date -Ru)
REL

for f in \
  "$COMPONENT/binary-$ARCH/Packages" \
  "$COMPONENT/binary-$ARCH/Packages.gz"; do
  size=$(stat -c%s "dists/$CODENAME/$f")
  md5=$(md5sum "dists/$CODENAME/$f" | awk '{print $1}')
  sha256=$(sha256sum "dists/$CODENAME/$f" | awk '{print $1}')
  {
    if ! grep -q '^MD5Sum:' "dists/$CODENAME/Release"; then
      echo "MD5Sum:"
    fi
  } >> "dists/$CODENAME/Release"
  echo " $md5 $size $f" >> "dists/$CODENAME/Release"
done

for f in \
  "$COMPONENT/binary-$ARCH/Packages" \
  "$COMPONENT/binary-$ARCH/Packages.gz"; do
  size=$(stat -c%s "dists/$CODENAME/$f")
  sha256=$(sha256sum "dists/$CODENAME/$f" | awk '{print $1}')
  {
    if ! grep -q '^SHA256:' "dists/$CODENAME/Release"; then
      echo "SHA256:"
    fi
  } >> "dists/$CODENAME/Release"
  echo " $sha256 $size $f" >> "dists/$CODENAME/Release"
done

# Optional signing.
if command -v gpg >/dev/null 2>&1 && [[ -n "${PAMM_GPG_KEY_ID:-}" ]]; then
  gpg --batch --yes -abs -u "$PAMM_GPG_KEY_ID" -o "dists/$CODENAME/Release.gpg" "dists/$CODENAME/Release"
  gpg --batch --yes --clearsign -u "$PAMM_GPG_KEY_ID" -o "dists/$CODENAME/InRelease" "dists/$CODENAME/Release"
  echo "Signed repository with key: $PAMM_GPG_KEY_ID"
else
  echo "warning: repository not signed (set PAMM_GPG_KEY_ID to sign)"
fi

popd >/dev/null

echo "APT repo built in: $REPO_DIR"
