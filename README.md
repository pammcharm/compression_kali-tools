# PAMM (Predictive Adaptive Multi-Model)

PAMM is a cross-platform archival compressor with two formats:
- `.pamm`: adaptive multi-engine archive with optional encryption and integrity
- `.pa`: fast single-engine mode

## Features
- Works on any file type (text, binary, executables, archives, media)
- File and folder compression/decompression
- Native C++ backend (`pybind11`) with adaptive engine selection
- Reversible executable-aware normalization for PE/ELF/Mach-O classes
- Optional AES-256-GCM encryption (`--password`)
- Integrity checks (SHA-256 + HMAC)
- CLI doctor command for runtime diagnostics

## Quick Use
```bash
# Compress (output inferred automatically)
pamm compress my_folder
pamm compress video.mkv --fast

# Explicit output and encryption
pamm compress my_folder -o backup.pamm --password "strong-passphrase"

# List archive contents
pamm list backup.pamm

# Extract (destination inferred automatically)
pamm extract backup.pamm
pamm extract backup.pamm -d ./restored

# Diagnostics
pamm doctor
pamm --help
```

## Kali Install

### User install (recommended)
Installs for current user, available in all your terminals:
```bash
./scripts/install_kali.sh --user
```
If you want installer to run `apt update` first:
```bash
./scripts/install_kali.sh --user --apt-update
```

### System install (all users)
Installs system-wide:
```bash
./scripts/install_kali.sh --system
```

### Build a `.deb` package
```bash
./scripts/build_deb.sh
sudo apt install ./dist/pamm_*_$(dpkg --print-architecture).deb
```

If you installed an older `pamm` package that ran apt/pip in `postinst`, remove it first:
```bash
sudo apt remove --purge pamm
sudo apt install ./dist/pamm_*_$(dpkg --print-architecture).deb
```

### Uninstall
```bash
./scripts/uninstall_kali.sh --user
./scripts/uninstall_kali.sh --system
```

## Shell Completion
Completion is installed automatically by `install_kali.sh`.

Manual generation:
```bash
pamm completion --shell bash
pamm completion --shell zsh
```

## One-shot local build/test run
```bash
./run_all.py --recreate-venv
```

## Benchmark Harness
```bash
.venv/bin/python benchmarks/benchmark.py /path/to/corpus --max-files 25
```
Tools used when available: `7z`, `zstd`, `xz`.

## APT Repository Distribution
You can publish PAMM as an APT repository for Kali users.

Local build of APT repo metadata:
```bash
./scripts/build_deb.sh
./scripts/build_apt_repo.sh
```

Publish to GitHub Pages (after git init/remote setup):
```bash
./scripts/publish_apt_github_pages.sh
```

Client install from APT source:
```bash
./scripts/install_apt_source.sh https://<user>.github.io/<repo>
# or signed mode
./scripts/install_apt_source.sh https://<user>.github.io/<repo> https://<user>.github.io/<repo>/pamm.gpg
```

Detailed guide: `APT_REPO.md`
