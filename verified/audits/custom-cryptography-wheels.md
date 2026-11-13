> **Reviewer note (added by the lead, 2026-11-13):** The FAIL verdicts below rest on the `cobblestone` module being "outside the expected cryptography surface". That was checked afterwards: `cobblestone.py`, `cobblestone.pyi`, `src/rust/src/cobblestone.rs`, docs and tests are all in the official PyPI `cryptography-50.0.2` sdist, and all 58 official wheels contain it, so it is upstream code. The custom wheels' 78 Python files are byte-identical to the official wheel's. The workflow findings (floating OpenSSL tag, unpinned build tools, version read from live GAM `main`) and the inability to verify the compiled module still stand. See `VERIFIED.md`.

💡agent-bootstrap 0.2.9 loaded.
I'll review the cryptography-wheels workflow and both custom wheels statically: clone source, unpinned tools, wheel Python and RECORD, binary inventory, and the path from build to release. No execution, imports, or network calls.The workflow is unpinned at several fetch points. Next I’ll unpack both wheels myself and check their Python, RECORD files, and native binaries against a normal cryptography abi3 layout.## Verdict

| Artifact | Verdict |
|---|---|
| `jay0lee/cryptography-wheels` workflow snapshot (`61b4ee3f…`, file on disk) | **REVIEW** |
| `cryptography-50.0.2-cp314-abi3-win_arm64.whl` (`a00bdd39…`) | **FAIL** |
| `cryptography-50.0.2-cp314-abi3-macosx_15_0_x86_64.whl` (`cd92c278…`) | **FAIL** |

Both wheels are real cryptography 50.0.2 abi3 builds from this pipeline (maturin, static OpenSSL 4.1.0, GitHub Actions paths under `cryptography-wheels`). RECORD matches. The Python package is the normal layout plus one extra native cipher, `cobblestone`, compiled from `src/rust/src/cobblestone.rs` into the same `_rust` extension. That module is the fail. The workflow does not patch it in; it also does not pin the source or the tools that compiled it, and the release job will publish whatever those builds emit.

Unpacked to `work-a2b/win_arm64` and `work-a2b/macosx_15_0_x86_64` with `python3 -I` and `zipfile` (bytes only). Nothing from the wheels was imported or executed.

## 1. What the workflow builds

The workflow does **not** build a pinned `v50.0.2` commit.

It clones the genuine URL `https://github.com/pyca/cryptography.git` (default branch), then checks out whatever version string is on **live** `GAM-team/GAM` `main`:

```135:174:repos/cryptography-wheels/.github/workflows/build_wheels.yml
      - name: Resolve pinned cryptography version from GAM
        shell: bash
        run: |
          echo "Fetching pyproject.toml from the GAM repository..."
          curl -sSL "https://raw.githubusercontent.com/GAM-team/GAM/main/pyproject.toml" -o gam_pyproject.toml
          # ...
          echo "CRYPTO_VERSION=$CRYPTO_VERSION" >> $GITHUB_ENV

      - name: Clone Cryptography
        shell: bash
        run: |
          git clone https://github.com/pyca/cryptography.git
          cd cryptography
          git checkout ${{ env.CRYPTO_VERSION }}
```

The regex allows only digits and dots (`[0-9.]+`), so this is not a shell-injection sink. It is also not a commit pin, not `refs/tags/…`, and not a `v` prefix. These wheels are version 50.0.2, so the run that produced them resolved `CRYPTO_VERSION=50.0.2` and `git checkout 50.0.2` succeeded. That shows the ref name, not that the ref was the upstream tag.

OpenSSL is a second clone, then a floating tag:

```70:78:repos/cryptography-wheels/.github/workflows/build_wheels.yml
          git clone https://github.com/openssl/openssl.git
          cd "${OPENSSL_SOURCE_PATH}"
          export LATEST_STABLE_TAG=$(git tag --list openssl-* | grep -v alpha | grep -v beta | sort -Vr | head -n1)
          echo "Checking out version ${LATEST_STABLE_TAG}"
          git checkout "${LATEST_STABLE_TAG}"
```

`no-shared` / `OPENSSL_STATIC=1` is why the extension has no `libssl` dependency. The tag filter drops only `alpha` and `beta`.

Unpinned installs and remote code, all over HTTPS with no digest:

| Step | What is fetched |
|---|---|
| `CIBW_BEFORE_BUILD` and the build step | `https://bootstrap.pypa.io/get-pip.py`, then `python get-pip.py` |
| same | `pip install uv` and `uv pip install setuptools-rust` (no versions) |
| build step | `pip install uv cibuildwheel` (no versions) |
| build backend | `CIBW_BUILD_FRONTEND: "build[uv]"`; wheel metadata says **maturin 1.16.0**, which is inside upstream's `maturin>=1.14.1,<2` and was resolved at build time |
| not in the workflow | `rustc` / Cargo, and `cargo-cyclonedx` 0.5.9 (recorded in the SBOM) |

SHA-pinned actions: `actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd`, `actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f`, `ilammy/msvc-dev-cmd@0b201ec74fa43914dc39ae48a89fd1d8cb592756`, `ilammy/setup-nasm@72793074d3c8cdda771dba85f6deafe00623038b`. Those SHAs were not checked against upstream (no network). Floating tags: `actions/download-artifact@v4`, `softprops/action-gh-release@v2`.

The repo snapshot matches `pins/cryptography-wheels/build_wheels.yml` (`diff -q` clean). `repos/cryptography-wheels.sha` is `61b4ee3f6736d0c94bf4d6f9675b117818139040`. There is no `.git` directory, so that commit was not recomputed. The tree is the workflow, an Apache LICENSE, a one-line README, and a normal Python `.gitignore`. No other workflow.

## 2. Python in the wheels

119 files each. One native module. No `.pth`, no `entry_points.txt`, no `setup.py`, no scripts, no `.pyc`, no path traversal, no encrypted zip entries.

Layout matches a maturin abi3 cryptography wheel: `cryptography/**/*.py`, stubs under `cryptography/hazmat/bindings/_rust/`, `dist-info` (`METADATA`, `WHEEL`, `RECORD`, licenses, CycloneDX SBOM), and a single extension.

`METADATA` on both is pyca's: name `cryptography`, version `50.0.2`, author `cryptography-dev@python.org`, homepage `https://github.com/pyca/cryptography`. `__about__.py` has `__version__ = "50.0.2"` and copyright 2013–2026. `__init__.py` only re-exports version metadata. `binding.py` loads the extension the usual way:

```14:15:work-a2b/win_arm64/cryptography/hazmat/bindings/openssl/binding.py
from cryptography.hazmat.bindings._rust import _openssl, openssl
from cryptography.hazmat.bindings.openssl._conditional import CONDITIONAL_NAMES
```

After converting Windows CRLF to LF, every `.py` and `.pyi` is byte-identical across the two wheels. The three real differences are expected: `RECORD` (hashes and the native filename), `WHEEL` (platform tag; macOS also has `Generator: delocate 0.13.0`, which is what cibuildwheel writes), and the SBOM (paths and timestamps).

Windows `WHEEL`:

```
Wheel-Version: 1.0
Generator: maturin (1.16.0)
Root-Is-Purelib: false
Tag: cp314-abi3-win_arm64
```

The macOS tag is `cp314-abi3-macosx_15_0_x86_64`, which matches `MACOSX_DEPLOYMENT_TARGET` taken from the `macos-15-intel` runner.

A scan of every `.py` / `.pyi` for `exec`, `eval`, `compile(`, `__import__`, `marshal`, `pickle`, `subprocess`, `socket`, `ctypes`, `urlopen`, and `verify=False` hit only ordinary cryptography code: Fernet and HOTP base64, PKCS7/SSH ASCII armor, and NIST curve orders in `ec.py`. HOTP builds an `otpauth://` string with `urllib.parse`; it does not open a connection (`hotp.py:9`, `hotp.py:42`).

**Anomaly, both wheels:** `cryptography/cobblestone.py` plus `cryptography/hazmat/bindings/_rust/cobblestone.pyi`. Nothing else imports it (`__init__.py` and `hazmat/__init__.py` do not).

```7:14:work-a2b/win_arm64/cryptography/cobblestone.py
from cryptography.hazmat.bindings._rust import (
    cobblestone as _cobblestone,
)

Cobblestone128Decryptor = _cobblestone.Cobblestone128Decryptor
Cobblestone128Encryptor = _cobblestone.Cobblestone128Encryptor
Cobblestone256Decryptor = _cobblestone.Cobblestone256Decryptor
Cobblestone256Encryptor = _cobblestone.Cobblestone256Encryptor
```

The stub is a stream-style API: `generate_key()`, `__init__(key, context)`, `update`, `update_into`, `finalize` (`cobblestone.pyi:7-33`). That is not AES, ChaCha, Fernet, HPKE, ML-KEM, or ML-DSA. Those others are present under their usual names and look in place. Confidence **high** that this module is in the wheels and is outside the expected cryptography surface. Confidence **medium** that the genuine pyca tag lacks it: the tag was not fetched (no network). The local tree `review/runtime/cryptography/WHEEL_cryptography-50.0.2-cp311-abi3-…` is not an independent baseline. It has the same 78 `.py` files, including this one, and it has no extension, no licenses, and no SBOM. Its sdist directory contains only `pyproject.toml`.

## 3. RECORD

Both RECORDs: 119 lines, SHA-256 urlsafe-base64, size checked against uncompressed bytes, **0 mismatches**, no missing files, no extra paths, no duplicate names. The `RECORD` line itself has an empty hash and size, which is the wheel format. macOS has 21 extra zip directory entries (`cryptography/`, `…/bindings/_rust/openssl/`, `dist-info/licenses/`, `dist-info/sboms/`). They are package directories, not extra files, and they are not RECORD entries.

## 4. Binaries

| File | Kind | Size | SHA-256 |
|---|---|---|---|
| `cryptography/hazmat/bindings/_rust.pyd` | PE32+ DLL, AArch64, Windows | 8,123,392 | `a42afa419c5368836ac050fdc3b3f755351618dba654ab421001059ba89bb290` |
| `cryptography/hazmat/bindings/_rust.abi3.so` | Mach-O 64-bit dylib, x86_64 | 11,176,664 | `256e6badc603bba7cd94bda9b964b981e29f4f40b03283b5169aff72c5bdd91a` |

No overlay past the PE sections or the Mach-O segments. The Mach-O binary is unsigned. Sections are the usual `.text/.rdata/.data/.pdata/.reloc` and `__TEXT/__DATA/__LINKEDIT`. No delay-load imports, no CLR directory.

**Linked libraries**

- macOS (`otool -L`): `@rpath/cryptography.hazmat.bindings._rust.abi3.so`, `/usr/lib/libiconv.2.dylib`, `/usr/lib/libSystem.B.dylib`. No `libssl`, `libcrypto`, or `libcurl`. Undefined symbols include `_dlopen` and `_socketpair` (316 undefined symbols total). No `posix_spawn`, `execve`, or `popen`.
- Windows imports: `python3.dll`, `bcryptprimitives.dll` (`ProcessPrng`), `bcrypt.dll` (`BCryptGenRandom`), `CRYPT32.dll` (cert store), `WS2_32.dll` (sockets, including `WSASocketA`), `KERNEL32.dll`, `ntdll.dll` (`NtWriteFile`, `RtlNtStatusToDosError`), `VCRUNTIME140.dll`, and `api-ms-win-crt-*` (`fopen`, `getenv`, and the usual CRT). No `winhttp`, `wininet`, `urlmon`, `shell32`, `CreateProcess`, `WinExec`, or `URLDownloadToFile`.

**Strings (printable runs only)**

Both binaries contain `OpenSSL 4.1.0 23 Oct 2026` (Windows at `0x598258`, macOS at `0x73e74e`). That matches the workflow's "latest stable tag" build on 2026-11-12, not a pinned OpenSSL.

URLs in the macOS binary: `https://cryptography.io/en/latest/faq/#why-can-t-i-import-my-pem-file`, `https://github.com/PyO3/pyo3/issues/576`, `https://github.com/pyca/cryptography/issues`, `https://github.com/dot-asm`. The Windows binary has the first three. No IPs other than OID arcs (`1.2.840.1.101.3.4…`). `ticket_appdata` and `derive_secret_key_and_iv` are OpenSSL TLS strings.

**Cobblestone is inside the extension, both platforms.**

- Windows: `cobblestone` at `0x55db2d`, `src\rust\src\cobblestone.rs` at `0x57ca68`, `PyInit_cobblestone` at `0x75ff56`, plus `Cobblestone128/256` `Encryptor`/`Decryptor` and `cryptography.hazmat.bindings._rust.cobblestone`.
- macOS: `src/rust/src/cobblestone.rs` at `0x7370bb`, `_PyInit_cobblestone` at `0x98cca5`, and Rust symbols `cryptography_rust::cobblestone::derive_keys`, `ChunkNonces::next`, `ChunkCipher::encrypt_chunk` / `decrypt_chunk`, `ChunkedEncryptor` / `ChunkedDecryptor` (`update`, `update_into`, `finalize`, `generate_key`).

So this is a source file of the `cryptography_rust` crate, compiled in, not a second DLL glued on later. `binding.py` loads that same extension on import. The Python wrapper is not on the import path; the code is still in the image.

SBOM (`cargo-cyclonedx` 0.5.9): 39 components, the cryptography crates plus the usual set (`openssl` 0.10.81, `openssl-sys` 0.9.117, `pyo3` 0.29.2, `asn1`, `pem`, …). No `cobblestone` crate, no `reqwest`/`hyper`. Non-file URLs are docs.rs and GitHub links in crate metadata. Build paths:

- Windows, `2026-11-12T18:12:53Z`: `C:/a/cryptography-wheels/cryptography-wheels/cryptography/src/rust`
- macOS, `2026-11-12T18:08:10Z`: `/Users/runner/work/cryptography-wheels/cryptography-wheels/cryptography/src/rust`

Those are GitHub-hosted runner paths for this repo. They tie these two files to this workflow's runners.

**Compiled code was not fully verified.** Strings and import tables cannot show what `derive_keys` or `encrypt_chunk` do. A reproducible check needs the pyca commit SHA that `50.0.2` resolved to on 2026-11-12, the OpenSSL commit for `openssl-4.1.0` (the version string is not a commit id), pinned `rustc`, maturin 1.16.0, cibuildwheel, delocate 0.13.0, and `cargo-cyclonedx` 0.5.9, then a rebuild with `maturin`'s locked `Cargo.lock` and a hash compare of `_rust.pyd` / `_rust.abi3.so`. Official PyPI wheels for these two tags are not in the tree; a PyPI wheel would also be a different OpenSSL and a different platform, so it would not match these binaries even if the Rust source matched.

## 5. Build to release

`release_wheels` runs on `ubuntu-slim` after every matrix leg succeeds. It downloads **all** artifacts with `actions/download-artifact@v4` (no name, no digest) and publishes every `all_wheels/**/*.whl` through `softprops/action-gh-release@v2`, `draft: false`, tag `release-<date>-<run_id>`. The job has `contents: write`.

Triggers are `push` (every branch), `workflow_dispatch`, and `cron: '0 10 * * *'`. Each success creates a new release. GAM installs whatever asset is latest:

```283:287:src/.github/workflows/build.yml
            gh release download --repo "jay0lee/cryptography-wheels" --pattern "*[^t]-win_arm64.whl" --clobber
            # ...
            gh release download --repo "jay0lee/cryptography-wheels" --pattern "*[^t]-macosx_15_0_x86_64.whl" --clobber
```

Injection points between compile and that download:

1. The two release actions are floating tags. A moved tag can swap the bytes that get published.
2. The build job uploads `wheelhouse/*.whl` with no allowlist and no hash. Any extra wheel that job writes is released.
3. There is no checksum, signature, or attestation on the release.
4. A push of this workflow, or the daily cron, rebuilds from unpinned GAM `main`, unpinned pyca ref, unpinned OpenSSL tag, and unpinned `get-pip.py` / pip packages, then becomes "latest".

These two wheels' SBOMs and the OpenSSL version string match that pipeline. There is no string evidence that a different binary was swapped in after the compile. The release job would not stop that if it happened.

## Findings

1. **Extra native cipher `cobblestone`.** `work-a2b/win_arm64/cryptography/cobblestone.py:7-14` (same file on macOS) and `…/_rust/cobblestone.pyi:7-33`. Native: `src/rust/src/cobblestone.rs` at Windows `0x57ca68` and macOS `0x7370bb`, `PyInit_cobblestone`, `derive_keys`, `ChunkCipher::{encrypt,decrypt}_chunk`. **Why:** the wheels identify themselves as pyca/cryptography 50.0.2, and this is a custom chunked cipher in that extension, with a key-derivation symbol, outside the usual primitive set. The workflow has no patch step, so it was in the tree that was compiled or it was inserted by an unpinned build tool. **Confidence:** high that it is present and unexpected; medium that the real pyca tag is clean, because that tag was not retrieved.

2. **Source and toolchain are unpinned.** Workflow lines 74–78, 139, 169–173, 180–193, 216–228. **Why:** GAM `main`, pyca ref, OpenSSL "latest" tag, `get-pip.py`, `uv`, `cibuildwheel`, and `setuptools-rust` are fetched and (for get-pip) executed with no hash. The shipped binaries contain `OpenSSL 4.1.0 23 Oct 2026`. **Confidence:** high.

3. **Release publishes unverified wheels as latest.** Workflow lines 204–228, consumed at `src/.github/workflows/build.yml:283-287`. **Why:** floating release actions, no digest, glob upload, every push and the daily cron cut a non-draft release. **Confidence:** high for the control gap. Low that these two files were replaced after build.

## Cleared

- Fernet/HOTP/PKCS7/SSH base64 and the `otpauth://` URI builder.
- `test_support.pyi`: certificate tag fields and `pkcs7_verify`, the usual test helper stub that ships beside the extension.
- ML-DSA, ML-KEM, HPKE, Argon2 modules: names and placement match a 50.x cryptography tree.
- Windows CRLF vs macOS LF: same text once newlines are normalized.
- macOS `Generator: delocate 0.13.0` and `@rpath` install name.
- Static OpenSSL (no `libssl`/`libcrypto` dylib), `libiconv` + `libSystem`, Windows `bcrypt` / `CRYPT32` / `WS2_32`.
- SBOM crate set and docs.rs/GitHub metadata URLs, including `https://github.com/dot-asm`.
- OID-like "IP" strings, OpenSSL `ticket_appdata` / `derive_secret_key_and_iv`.
- `checkout` expression injection: version characters are only `[0-9.]`.
- Repo name `pyca/cryptography` and `openssl/openssl` are the real upstream URLs, not lookalikes. `jay0lee/cryptography-wheels` is a separate builder, and the wheel name stays `cryptography`.
- `.gitignore` is a stock Python ignore file. No second workflow.

## Coverage

Reviewed the workflow on disk, both assigned wheels' zip metadata, RECORD, all `.py`/`.pyi`/`METADATA`/`WHEEL`, both SBOMs, and printable strings plus PE imports / Mach-O load commands. Did not execute, import, or disassemble the native code. Did not contact GitHub or PyPI, so action SHAs and the pyca `50.0.2` tag contents were not confirmed remotely. A third wheel is in `artifacts-custom` and was not part of this review: `cryptography-50.0.2-cp314-abi3-macosx_26_0_arm64.whl`, sha256 `4578a42a70c39e47c9b8cd3277be99d82f8a5ba6307971a3cba00a605377eed1`.

**VERDICT:** workflow **REVIEW**. `win_arm64` wheel **FAIL**. `macosx_15_0_x86_64` wheel **FAIL**.
