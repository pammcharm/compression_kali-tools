# Publishing PAMM via APT

## 1) Prerequisites
- Project hosted in a GitHub repo
- GitHub Pages enabled for `gh-pages` branch
- Optional but recommended: GPG signing key

## 2) GitHub secrets (for signed repo)
- `PAMM_GPG_PRIVATE_KEY`: ASCII armored private key
- `PAMM_GPG_KEY_ID`: key ID/fingerprint used for signing

If secrets are not set, repo publishes unsigned metadata.

## 3) Publish
Use GitHub Release publish event or run workflow manually:
- Workflow: `.github/workflows/publish-apt.yml`

## 4) Client install (Kali)
Signed repo:
```bash
./scripts/install_apt_source.sh https://<user>.github.io/<repo> https://<user>.github.io/<repo>/pamm.gpg
```

Unsigned repo (not recommended):
```bash
./scripts/install_apt_source.sh https://<user>.github.io/<repo>
```

Then users can do:
```bash
sudo apt update
sudo apt install pamm
```

## 5) Local dry run
```bash
./scripts/build_deb.sh
PAMM_GPG_KEY_ID=<your-key-id> ./scripts/build_apt_repo.sh
```
