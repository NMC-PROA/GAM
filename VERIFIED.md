# Verified branch `verified/7.50.00`

Base: upstream `GAM-team/GAM` `main` @ `4cbf0e5bdacf7eee5009a67ec12c736fd5dc0d6e` (v7.50.00 + 1 commit, 2026-11-05).
Changes on top of that commit: lock files, pinned CI references, and this folder. No GAM source file under `src/` was changed.
Audited and pinned: 2026-11-13.

## What "verified" means here

- **Malware / supply-chain review only.** Memory-safety bugs and ordinary vulnerabilities were out of scope.
- **Static only.** Nothing from the audited artifacts was executed during review. The only execution was the install test below, in an isolated OrbStack VM.
- **Compiled code is not verified.** Native binaries (`cryptography` `_rust`, `lxml`, `protobuf`, `pyscard`, PyInstaller bootloaders, the Python+OpenSSL toolchain archives) were inventoried and hash-pinned but not disassembled.
- Reviewers: Grok 4.7 at high effort (dependency, action and wheel audits), plus the earlier GAM source audit (Codex GPT-6.1 Sol high fast; Grok 4.7 build-fast xhigh). Reports are in `verified/audits/`. Reviewer claims were spot-checked, not all re-derived.

## Pins

| What | Where | Pinned by |
|---|---|---|
| 60 runtime packages (incl. `[yubikey]` extra), all platforms, Python >= 3.11 | `requirements.lock` | `==` + SHA-256 of every wheel and sdist, resolved with `--exclude-newer 2026-11-05`, `--no-build` |
| 19 build tools (PyInstaller, StaticX, hatchling, pip, setuptools, wheel, ...) | `build-requirements.lock` (from `build-requirements.in`) | same |
| `patchelf-wrapper` 1.2.0 (sdist only; compiles embedded patchelf 0.11) | `.github/locks/patchelf-wrapper.lock` | SHA-256 |
| `pyscard` (Windows pre-build step) | `.github/locks/pyscard.lock` | SHA-256 |
| Build backend | `pyproject.toml` | `hatchling==1.29.0` (was `<1.30.0`) |
| GitHub Actions | `.github/workflows/*.yml` | full commit SHA |
| `jay0lee/python-openssl-latest` | `build.yml` | commit `7008438` **and** `version: v1.2026.11.08.1052`, plus post-install SHA-256 check (`.github/actions/verify_toolchain.py`, `.github/locks/toolchain-sha256.txt`) |
| Custom `cryptography` wheels (Windows ARM64, macOS x86_64) | `build.yml` | release `release-2026-11-12-43274931471`, SHA-256 checked before install |
| rustup / Rust (macOS build) | `build.yml` | rustup 1.29.3 binary with SHA-256, Rust 1.100.0 |
| `get-pip.py` | `build.yml` | pypa/get-pip commit `8c42746`, SHA-256 |
| Inno Setup | `build.yml` | `choco ... --version=6.7.1` (version only) |
| Scheduled auto-upgrade / auto-commit workflows | `upgrade_deps.yml`, `get-cacerts.yml` | schedules removed; manual `workflow_dispatch` only |

## Install from source

```
python3.11+ -m venv .venv && . .venv/bin/activate
pip install --require-hashes --no-deps -r build-requirements.lock
pip install --require-hashes --no-deps -r requirements.lock
pip install --no-deps --no-build-isolation .
```

Tested 2026-11-13 in an Ubuntu 24.04 aarch64 VM on Python 3.12: `pip check` clean and `gam version` reports 7.50.00. Needed apt packages on Linux because `pyscard` builds from sdist there: `swig libpcsclite-dev python3-dev build-essential pkg-config`. `staticx` was left out of that test (its only wheel is x86_64; other platforms build from the locked sdist). Python 3.10 is not supported by this lock: upstream declares `>=3.10` but `filelock==4.2.0` requires 3.11.

Do not use `gam-install.sh` or the upstream release binaries to get "verified" code: they are built by upstream CI, not by this branch.

## Audit results

| Artifact set | Verdict |
|---|---|
| 60 runtime + 19 build PyPI packages | No FAIL. 40 of 79 have PyPI trusted-publisher attestations tying them to the upstream repo and workflow. The rest depend on the maintainer's PyPI account. |
| `modern-httplib2` 1.32.1.post1 | PASS. Wheel and sdist `.py` files identical to git tag `v1.32.1-1`; attested to GAM-team/modern-httplib2. |
| `jay0lee/python-openssl-latest` action | REVIEW. See residual risk 1. |
| Custom `cryptography` wheels | See residual risk 2. The reviewer's FAIL (on the `cobblestone` module) was a false positive. |
| GAM source (`src/`) | No backdoor or exfiltration found (earlier audit, `verified/audits/gam-source-2026-11-06/`). Findings F3 (GData proxy path without certificate verification), F8 (OAuth URL shortener) and F9 (GCS path join) remain unfixed in source. |

Resolved review items:
- `charset-normalizer`: the single wheel/sdist difference is the standard `delvewheel` DLL-loader patch in the `win_arm64` wheel.
- `cobblestone` in `cryptography`: present in the official PyPI sdist (with docs and tests) and in all 58 official wheels, so it is upstream code. The Python files of both custom wheels are byte-identical to the official wheel's.
- `pywin32-ctypes`: author email domain `enthough.com` is an old upstream typo; no code contacts it.

## Residual risk (read before trusting binaries built from CI)

1. **Toolchain archive.** The upstream installer never checks digests and drops to unverified TLS if `certifi` is missing. The pinned post-install check detects a swapped archive but runs after the installer has already executed it, and CI credentials are loaded earlier. Prefer replacing the action with `actions/setup-python` if you do not need OpenSSL 4.
2. **Custom `cryptography` wheels.** The two wheels exist because PyPI has no `win_arm64` or `macosx_15_0_x86_64` wheel. They are built by a third-party repo that clones `pyca/cryptography` by version string read from live GAM `main`, builds against the latest OpenSSL tag, and installs unpinned build tools. Their Python layer matches upstream exactly. Their native `_rust` module cannot be verified statically; they are pinned by hash to one release only.
3. **Unpinned and unverified fetches that remain:** apt packages on runners, `choco` (version only), `actions/*` internals, and the build steps of the two `jay0lee/*` repos.
4. **Source findings above** are not fixed on this branch.
5. **CI edits are untested** on GitHub Actions. Run them on a fork first.
6. **Attestation covers the upload, not the code.** A maintainer-signed release can still contain a malicious commit.

## Updating

Do not enable scheduled upgrades. To move a pin: re-resolve with `uv pip compile ... --generate-hashes --no-build`, diff the lock, re-run the audits on changed artifacts, and update this file.
