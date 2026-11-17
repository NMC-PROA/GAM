# NMC-PROA pinned GAM

Pinned, audited fork of [GAM-team/GAM](https://github.com/GAM-team/GAM) for NMC-PROA.

- **Use branch `pinned/nmcpinned-261117`.** `main` is an unmodified mirror of upstream and is not audited.
- **Base:** upstream v7.50.00 (`4cbf0e5b`). `src/` is unchanged from upstream; only lock files, CI pins and docs were added.
- **Branch naming:** `pinned/nmcpinned-YYMMDD`. A new dated branch is cut each time the pin is moved.

## Install (from source, hash-checked)

Python 3.11 or newer.

```
python3 -m venv .venv && . .venv/bin/activate
pip install --require-hashes --no-deps -r build-requirements.lock
pip install --require-hashes --no-deps -r requirements.lock
pip install --no-deps --no-build-isolation .
gam version
```

Linux also needs `swig libpcsclite-dev python3-dev build-essential pkg-config` (pyscard builds from source there).

Do **not** use `gam-install.sh` or upstream release binaries: they are built by upstream CI, not by this branch.

## What is verified

- All 60 runtime and 19 build packages are pinned by SHA-256; 40 of 79 have PyPI attestations tying them to their upstream repo.
- CI actions are pinned to commit SHAs; rustup, get-pip, the custom `cryptography` wheels and the Python+OpenSSL toolchain archive are hash-checked.
- Scope was malware and supply chain only (no memory-safety or general bug hunting). Static review; compiled code was not disassembled.

## What is not

- The custom `cryptography` wheels (Windows ARM64, macOS x86_64) and the Python+OpenSSL toolchain archive cannot be fully verified.
- The CI changes have not been run on GitHub Actions yet. Test on this fork before relying on a CI-built binary.
- Source findings F3, F8, F9 are noted, not fixed.

Details, audit results and the full risk list: [`VERIFIED.md`](VERIFIED.md). Reviewer reports: `verified/audits/`.

## Do not auto-update

- **Never run `gam version update` or `gam version install`** if you move to a newer GAM. Those commands (added upstream in 7.52.00; not in this branch) download upstream binaries and replace the audited build. See `VERIFIED.md`, "Upstream 7.51.00 to 7.52.03".
- Scheduled dependency-upgrade workflows are disabled here. Keep them off.

## Moving the pin

1. Sync the fork's `main` from upstream and review the diff.
2. Branch from the new `main`; re-lock with `uv pip compile --generate-hashes --no-build`.
3. Re-audit the changed artifacts, update `VERIFIED.md`, push `pinned/nmcpinned-<new date>`, and set it as the default branch.
