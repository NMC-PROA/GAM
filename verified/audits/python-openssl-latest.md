💡agent-bootstrap 0.2.9 loaded.
I'll review the pinned action statically: inventory the tree, then read the install path, patches, and workflows for supply-chain indicators.The action installer is the main path. Next I’ll read the build scripts, patches, and workflows, and check whether the SHA256 helper is ever used.## Verdict

**`jay0lee/python-openssl-latest` @ `7008438716fd6ba2344f7796f68d52004d567a4d` (tree reviewed): REVIEW**

No hidden backdoor, obfuscated payload, or hardcoded exfiltration endpoint turned up in this tree. The consumer install path still turns TLS verification off in the common case, never checks the SHA256 it claims to check, and then runs the downloaded interpreter with the job environment. Pinning this commit plus `version: v1.2026.11.08.1052` fixes the installer source and the release **tag name**. It does not fix or verify the toolchain bytes.

The prebuilt Python/OpenSSL archives are not in this tree, so they have no malware verdict.

This checkout has no `.git` directory. The commit id above is the assignment label; it was not re-derived from git metadata.

---

## 1. What is downloaded, from where, and how it is checked

The action runs only `scripts/install.py` (`action.yml` lines 70–108). `install-python-openssl.sh` is a separate local installer and is not on that path.

With `version: v1.2026.11.08.1052` and the default `repository`, the installer does two HTTPS GETs:

1. Release metadata: `https://api.github.com/repos/jay0lee/python-openssl-latest/releases/tags/v1.2026.11.08.1052` (`scripts/install.py` lines 142–146).
2. Whatever URL is in the chosen asset’s `browser_download_url` (lines 266–270). There is no host allowlist. A normal GitHub release puts that URL on `github.com`; the code trusts the JSON.

Asset choice is the first name that contains the runner label and the arch string (`x64` or `arm64`), with Windows and macOS aliases added (`scripts/install.py` lines 221–247). It does not read `manifest.json`. It does not compare a digest. `compute_sha256` is defined at lines 65–70 and has no call site.

```266:275:scripts/install.py
    download_dir = os.environ.get("RUNNER_TEMP", "/tmp")
    archive_path = os.path.join(download_dir, selected_asset["name"])
    download_url = selected_asset["browser_download_url"]
    download_file(download_url, archive_path, args.token)

    # Extract
    if os.path.exists(install_dir):
        shutil.rmtree(install_dir)
    extract_archive(archive_path, install_dir)
```

The module docstring says the script “verifies SHA256” (`scripts/install.py` lines 8–9). The README says a pin of `@v1.<calver>` pins “both action code and runtime bundle” (`README.md` lines 57–58) and that releases ship checksums and `manifest.json` (`README.md` line 20). The action never consults those files. **High.** This is a claim/behavior gap, not a second hidden downloader.

`version` values `latest` and `v1` use `/releases/latest` (`scripts/install.py` line 142). A pin of the action by commit SHA alone does the same: `github.action_ref` is a SHA, the regex in `action.yml` lines 80–87 does not treat it as a release tag, and the bundle becomes `latest`.

### `CERT_NONE` is reachable whenever `certifi` is missing or fails

```39:47:scripts/install.py
def create_ssl_context():
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
    except Exception:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx
```

Both the release API call (line 135) and the archive download (line 59) use this context.

It runs when `import certifi` raises, or when `certifi.where()` / `load_verify_locations` raises. `certifi` is not part of the standard library. The action starts `python3` or `python` already on the runner (`action.yml` lines 61–67), which is the image interpreter, not the bundle being installed. On a runner image that has not installed `certifi` for that interpreter, this is the normal path, not a rare error path.

`ssl.create_default_context()` already verifies with the system trust store. The `except` branch does not keep that context. Any failure of the optional `certifi` bundle disables hostname and certificate checks. The same helper is copied in `scripts/discover_matrix.py` lines 88–97 and is used for every GitHub API call in the build pipeline. **High** that verification is off in the common case. **Medium** that this is an accidental fallback rather than an intentional backdoor: it is duplicated, unobfuscated, and sits on the obvious “optional CA bundle” path. Effect is the same either way: release JSON and archive bytes are unauthenticated, and the bearer token below is sent to that peer.

The shell installer does not do this. `curl` / `wget` there have no `-k` / `--no-check-certificate` (`scripts/install-python-openssl.sh` lines 109–120 and 233–236).

### Other integrity notes on the install path

- Tar extraction uses `filter="tar"` when that keyword exists, and on `TypeError` / `AttributeError` falls back to unfiltered `extractall` (`scripts/install.py` lines 166–170). Zip extraction has no filter (lines 161–163). A malicious archive can use that fallback to write outside the install directory. **Medium**, and only relevant once the archive is attacker-controlled.
- On Linux the installer may `sudo apt-get install -y -qq patchelf` with no version pin (lines 281–285). Apt’s own signature check is left on. **Low** as a malware indicator; it is another unpinned fetch on the credentialed runner.
- After extract, the new `python3` / `python.exe` is executed (`-VV`, `import ssl`, version probes) with `os.environ.copy()` (lines 417–432 and 465–466).

The shell script’s checksum is optional and same-origin. It always asks for `/releases/latest` (line 108). It verifies only if `{download_url}.sha256` downloads successfully and a local hash tool exists (lines 239–265). A missing sidecar, a failed sidecar download, or no `sha256sum` / `shasum` / `python3` skips the check and still extracts. The expected hash is published by the same release as the archive. **Medium.** The action does not use this script.

---

## 2. Secrets and tokens

The action default token is `${{ github.token }}` (`action.yml` lines 29–32). It is placed on the installer command line (`action.yml` lines 90–93) and sent as `Authorization: Bearer` to the API URL and to `browser_download_url` (`scripts/install.py` lines 50–61 and 133–140). No allowlist limits that host. With `CERT_NONE`, a network attacker who answers those TLS sessions receives the token and chooses the bytes that are then executed. **High** for that path.

Nothing else in this tree collects credentials and posts them. There is no webhook, DNS hook, or scan of signing-key files. `discover_matrix.py` sends `GITHUB_TOKEN` only to hardcoded `api.github.com` URLs (lines 100–114, 123, 144, 357, 387), again through the `CERT_NONE` fallback. The build workflow’s token is `contents: write` (`build-and-release.yml` lines 34–37).

The downloaded interpreter is a different boundary. Verification and every later step run it with the job environment, which is where GitHub places `GITHUB_TOKEN` and where a signing job places cloud and code-signing credentials. The scripts do not themselves transmit that environment. A backdoored archive would see it, and this installer will run that archive. **High** that the environment is inherited. That is what a toolchain setup action does; the missing digest and the TLS fallback are what make it an attack path.

`scripts/validate_runtime.py` GETs `https://www.googleapis.com/discovery/v1/apis` with a User-Agent and a verifying context (lines 83–128). It does not attach tokens. `action.yml` does not call it. The test workflow does, using the just-installed interpreter (`test-action.yml` lines 70–73).

---

## 3. Patches

`patches/py314-ossl4.diff` (68 lines) changes `Modules/_ssl.c` in three ways:

- For `OPENSSL_VERSION_NUMBER >= 0x40000000L`, it defines `OPENSSL_NO_SSL3`, `OPENSSL_NO_TLS1`, `OPENSSL_NO_TLS1_1`, `OPENSSL_NO_TLS1_2`, and the matching `*_METHOD` macros (diff lines 9–18).
- It adds `const` to X509 name helpers (OpenSSL 4 signature changes).
- It wraps `PROTOCOL_TLSv1`, `PROTOCOL_TLSv1_1`, and `PROTOCOL_TLSv1_2` in the matching `#ifndef`s, so those constants are omitted.

It does not mention `SSL_VERIFY`, hostname checks, trust anchors, or `CERT_NONE`. The OpenSSL configure lines disable TLS 1.0 and 1.1 (`no-tls1`, `no-tls1_1`) and do not pass `no-tls1_2` (`scripts/build_openssl.sh` lines 27–55, `scripts/build_openssl.ps1` lines 49–77). **Medium** that the diff is a binding compatibility shim for removed OpenSSL 4 method symbols. Residual uncertainty: those `OPENSSL_NO_*` macros affect every later `#ifndef` in `_ssl.c`, and that file is not in this tree, so side effects on default minimum protocol cannot be confirmed from here.

On Unix the patch is applied with `patch -p1 -N < ... || true` (`scripts/build_python.sh` line 54), so a failed or partial apply continues the build. The Windows script checks that `OPENSSL_NO_SSL3_METHOD` landed in `_ssl.c` and aborts if it did not (`scripts/build_python.ps1` lines 50–62). **Medium** as a build-integrity hole on Unix, not as hidden patch content.

`patches/windows/openssl.props` only sets include and library directories and links `libcrypto` / `libssl` plus `ws2_32`, `crypt32`, `advapi32`, and `user32` for `_ssl` and `_hashlib`. No extra source file, no custom CA, no verify-mode flag.

---

## 4. Where the build gets Python and OpenSSL

Unix and Windows build scripts clone these URLs when the source dir has no `configure` / `Configure` / `PCBuild\build.bat` yet:

- `https://github.com/openssl/openssl.git`
- `https://github.com/python/cpython.git`

(`scripts/build_openssl.sh` lines 65–76, `scripts/build_python.sh` lines 31–40, `scripts/build_openssl.ps1` lines 20–30, `scripts/build_python.ps1` lines 26–36.)

They then `git checkout` `openssl-<version>` or `v<version>`, or the raw version string if that tag does not resolve. There is no commit SHA, no `git verify-tag`, and no checksum of the tarball. If the source directory already contains a configure script, checkout is skipped and whatever tree is there is built. The workflow uses a fresh `RUNNER_TEMP`, so that skip is not hit by `build-and-release.yml` as written.

The version string comes from `discover_matrix.py`, which lists tags on `python/cpython` and `openssl/openssl` and keeps `vX.Y.Z` / `openssl-X.Y.Z` (`discover_matrix.py` lines 121–160). API failure falls back to hardcoded `3.14.7` and `4.0.2`. Those API calls use the `CERT_NONE` helper, so a network attacker can choose which dotted version is checked out. The clone URL itself stays on the canonical repos, and git is not told `GIT_SSL_NO_VERIFY`. Tag signatures are still not checked. **High** that upstream identity is “whatever tag name GitHub (or a MITM of the API) returned.”

Windows then runs `PCBuild\get_externals.bat --no-openssl` (`scripts/build_python.ps1` lines 79–83). That script is not in this tree. This repo does not pin or re-hash those externals.

Other unpinned build fetches in `build-and-release.yml`:

- `actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7`, `actions/download-artifact@v8` (tag, not SHA)
- `choco install nasm -y` (line 126)
- `sudo apt-get install` of compilers and libraries with no versions (lines 133–134)

`--with-ensurepip=upgrade` is passed to CPython configure (`scripts/build_python.sh` line 82). These scripts contain no pip URL of their own. Whether that configure switch contacts the network is behavior of the cloned CPython tree.

---

## 5. Release trust model, and whether the pin floats

The publish job builds `manifest.json` and `*.sha256` from the same artifacts it uploads (`build-and-release.yml` lines 410–434 and 322–379). Those checksums are unsigned and are produced by the same workflow as the binaries. They detect a truncated download only if a client checks them. `install.py` does not.

“Immutable” is a comment, not a lock:

- If the tag already exists and `force_rebuild` is true, the job runs `gh release upload "$TAG" ./release-assets/* --clobber` (lines 464–467).
- Otherwise it skips the build when `gh release view` succeeds (lines 88–90). That is a workflow convention.
- Nothing in this tree enables GitHub’s immutable-releases repository setting.
- Every successful publish force-moves the git tag `v1` (`git tag -fa v1` and `git push origin v1 --force`, lines 476–485).

A release asset is chosen by substring, first hit in API order. An extra asset whose name contains the runner label and arch is eligible. Alias copies (`xcode-*` to `macos-*`, `windows-latest` also published as `windows-2025`) are an intentional second name for the same bytes (lines 340–350 and 368–377). `BUILD_INFO.txt` inside the archive is printed as the build summary if present (`scripts/build_info.py` lines 248–268), so that text is whatever the archive author wrote.

**What the requested pin actually freezes**

| Input | What stays fixed | What still moves |
|---|---|---|
| Action `uses:` at commit `70084387…` | `action.yml` and `scripts/install.py` in that commit | — |
| `version: v1.2026.11.08.1052` | The release tag string requested from the API | Asset bytes, asset URLs, and which matching filename wins |
| Neither input records a digest | — | `.sha256` / `manifest.json` on the release can be replaced together with the archive (`--clobber`, or any release edit outside this workflow) |

So SHA + `version: v1.2026.11.08.1052` is a fixed installer and a fixed tag name. It is not a fixed, verifiable toolchain. A later change to the release assets is accepted and executed on the signing runner, and under the `certifi` failure path that download is not even TLS-authenticated.

No typosquat showed up in the URLs. Clones point at `github.com/openssl/openssl` and `github.com/python/cpython`. The default repo is `jay0lee/python-openssl-latest`. The `repository` input can retarget the download if the calling workflow sets it (`action.yml` lines 9–12). Account ownership, tag protection, and the live release were not checked.

---

## Coverage

Reviewed in full: `action.yml`, both workflows, `install.py`, `install-python-openssl.sh`, `build_openssl.sh`, `build_python.sh`, `build_openssl.ps1`, `build_python.ps1`, `setup_msvc.ps1`, `validate_runtime.py`, `discover_matrix.py`, `build_info.py`, `patches/py314-ossl4.diff`, `patches/windows/openssl.props`, and `README.md`. The tree listing matches `pins/python-openssl-latest/tree.txt` (20 files, no binaries). Tests were searched for network, hash, and `exec` use; they are unit tests of matrix parsing and the build-info formatter, not part of the install path.

Not reviewed, because they are not in the tree: the release archives and their `python` / `openssl` binaries, `PCBuild\get_externals.bat` and the externals it fetches, the CPython and OpenSSL trees that get checked out, the resolved SHAs of `actions/*@v7` and `@v8`, GitHub release immutability settings, and tag signatures. Nothing was executed, imported, installed, or fetched.

## Cleared

- `validate_runtime.py` base64 is absent; the `base64` use in `discover_matrix.py` line 390 decodes the GitHub API `content` field of `actions/runner-images`’s README.
- `zlib`, `hashlib`, and HMAC in `validate_runtime.py` are local round-trips. The HMAC key is the literal `b"secret-key"` (line 355).
- OpenSSL `no-tls1`, `no-tls1_1`, `no-weak-ssl-ciphers`, and the cipher disables are build hardening flags. They do not turn verification off.
- System CA paths are copied or symlinked into the install (`install.py` lines 382–395, `build_openssl.sh` lines 104–112). No private root is installed.
- `setup_msvc.ps1` only runs `vcvarsall.bat` and writes the resulting environment into `GITHUB_ENV` / `GITHUB_PATH`. It does not download code.
- Rewriting `_sysconfigdata` to strip `-Wl,-rpath` (`install.py` lines 302–317) and `patchelf --remove-rpath` stay on the extracted tree. No new code is fetched there.
- The shell installer edits `~/.bashrc`, `~/.zshrc`, and `~/.bash_profile` to prepend `$HOME/bin` (lines 336–424). That is local PATH persistence, and the action does not invoke it.
- No `setup.py`, `.pth`, entry points, `eval` / `exec` of decoded blobs, `marshal`, or `curl | sh`.
