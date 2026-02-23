# PAMM (Predictive Adaptive Multi-Model)

![PAMM App Logo](logo/logo1.png)

PAMM is a cross-platform compressor/archiver with two formats:
- `.pamm`: adaptive multi-engine archive with optional encryption and integrity
- `.pa`: fast single-engine mode

## Features
- Compress and extract files or folders
- Native C++ backend (`pybind11`) with adaptive engine selection
- Optional AES-256-GCM encryption (`--password`)
- Integrity checks (SHA-256 + HMAC)
- CLI diagnostics (`pamm doctor`)

## Quick Start
```bash
# Compress
pamm compress my_folder
pamm compress my_file.bin --fast

# Encrypt
pamm compress my_folder -o backup.pamm --password "strong-passphrase"

# List archive contents
pamm list backup.pamm

# Extract
pamm extract backup.pamm
pamm extract backup.pamm -d ./restored
```

## Install (Kali)
```bash
# User install
./scripts/install_kali.sh --user

# System install
./scripts/install_kali.sh --system
```

Build and install `.deb` manually:
```bash
./scripts/build_deb.sh
sudo apt install ./dist/pamm_*_$(dpkg --print-architecture).deb
```

## APT Repository
Build and publish APT repo metadata:
```bash
./scripts/build_apt_repo.sh
./scripts/publish_apt_github_pages.sh
```

Detailed APT guide: `APT_REPO.md`

## Development
```bash
./run_all.py --recreate-venv
```
