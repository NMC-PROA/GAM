💡agent-bootstrap 0.2.9 loaded.
I'll review the five pinned artifacts statically: provenance, install hooks, and the flagged code paths, with no execution or network calls.Triage shows no install-hook flags and no wheel/sdist Python diffs. Next I’ll read metadata, build scripts, and every flagged call site.Build metadata matches the known projects. I’ll scan the Python for exfiltration, dynamic execution, and install hooks, and read each hit in context.The extracted wheels look source-only. I’ll read the dynamic-exec, network, and build-script sites next, including lxml’s wheel build script.## Verdicts

| Package | Version | Provenance | Verdict | Reason |
|---|---|---|---|---|
| yubikey-manager | 5.9.2 | attested 0/2; PyPI account only; uploaded 2026-06-30; Homepage `https://github.com/Yubico/yubikey-manager` | **PASS** | No malware indicators in the Python wheel or build metadata. |
| fido2 | 2.2.1 | attested 0/2; PyPI account only; uploaded 2026-06-29; Homepage `https://github.com/Yubico/python-fido2` | **PASS** | No malware indicators in the Python wheel or build metadata. |
| cffi | 2.1.1 | attested 0/4; PyPI account only; uploaded 2026-08-03; source `https://github.com/python-cffi/cffi` | **PASS** | Python and build scripts match upstream CFFI. Native `_cffi_backend` not disassembled. |
| protobuf | 7.36.2 | attested 0/4; PyPI account only; uploaded 2026-09-17; Homepage `https://developers.google.com/protocol-buffers/` | **PASS** | Pure-Python wheel and `setup.py` match upstream protobuf. upb binaries not disassembled. |
| lxml | 6.1.3 | attested 0/4; PyPI account only; uploaded 2026-09-02; Homepage `https://lxml.de/`, source `https://github.com/lxml/lxml` | **PASS** | Python and build scripts match upstream lxml. Extension modules not disassembled. |

Names, authors, and URLs match the well-known projects: Dain Nilsson `<dain@yubico.com>` for both Yubico packages; Armin Rigo and Maciej Fijalkowski, maintainers Matt Davis and Matt Clay, for cffi; `protobuf@googlegroups.com` for protobuf; `lxml@lxml.de` for lxml. No typosquat or ownership mismatch in the metadata. TRIAGE flags are empty for all five. Wheel Python matches the sdist (yubikey-manager 61 files, fido2 40, cffi 1980 comparisons, protobuf 406, lxml 4375). lxml’s only wheel-only Python files are four empty `lxml/includes/**/__init__.py` markers that `setup.py` writes during a static build.

None of these artifacts have a PEP 740 attestation. Identity rests on the maintainer’s PyPI account. That is a trust gap, and it is not by itself a malware indicator.

## Per-package notes

**yubikey-manager.** `pyproject.toml` publishes both `ykman` and `yubikit` from this sdist (`packages = [{ include = "yubikit" }, { include = "ykman" }]`). That is the current upstream layout, not a second package dropped in beside it. The only entry point is `ykman=ykman._cli.__main__:main`. Build backend is `poetry.core.masonry.api`. No `.pth`, no binaries.

**fido2.** No entry points. Build backend is `poetry.core.masonry.api`. `fido2/rpid.py` loads `fido2/public_suffix_list.dat` at import. RECORD lists that file (`sha256=ggjwyRjGyzq3e0hGNfyGg8lMv_-Bi-gZUJCOiBpfi-I`, 333138 bytes). It was not in the extracted tree, so its bytes were not reviewed.

**cffi.** Entry points are the documented ones: console script `cffi-gen-src` and distutils keyword `cffi_modules = cffi.setuptools_ext:cffi_modules`. `setup.py` compiles local `src/c/_cffi_backend.c` and asks the local `pkg-config` / `brew --prefix libffi` for libffi. The representative wheel’s RECORD contains one extension, `_cffi_backend.cpython-311-x86_64-linux-gnu.so`, plus the usual `_cffi_*.h` headers. Those binaries and headers were not extracted. TRIAGE counts 99 binaries across the release, all `_cffi_backend` for the platform matrix (including iOS). No unexpected executable names in the sample.

**protobuf.** Representative artifact is the `py3-none-any` wheel: Python only, no entry points. `__init__.py` and `runtime_version.py` both say 7.36.2. `setup.py` builds `google._upb._message` from in-tree `upb/**/*.c`, `python/*.c`, and `utf8_range/*.c`. The six binaries in TRIAGE are `google/_upb/_message.abi3.so` or `.pyd` on the other wheels. They were not extracted. METADATA’s description body is the literal `UNKNOWN`; the rest of the metadata (author, homepage, BSD license, `Requires-Python: >=3.10`) is consistent with the Google package.

**lxml.** Representative RECORD lists the expected extensions: `etree`, `objectify`, `builder`, `sax`, `_elementpath`, `html/diff`, `html/_difflib` (7 `.so` files on this wheel). TRIAGE counts 1135 binaries across the platform matrix; the sample is those same module names. No stray executables in the sample. `pyproject.toml` pins static-dep versions (`ZLIB_VERSION=1.3.2`, `LIBXML2_VERSION=2.14.6`, `LIBXSLT_VERSION=1.1.43`, and the Windows override set). The downloader that would fetch those tarballs (`setupinfo.py` / `buildlibxml.py`) is not in the extracted sdist, so hash checks on those downloads were not visible.

## Cleared

These sites matched the pattern scan and are expected for these libraries.

- `ykman/_cli/script.py:107` — `exec(script_body, {})`. This is the documented `ykman script FILE` command. It runs only after a confirmation prompt unless `--force` is passed, and the warning text says scripts can harm the YubiKey and the computer. It does not run at install.
- `ykman/pcsc/__init__.py:241` and `:252` — `subprocess.call(["pkill", "-9", "scdaemon"])` and `pkill -HUP yubikey-agent`, fixed argument lists, no shell. Used only after an exclusive CCID open fails, to drop known holders of the reader. Windows uses WMI to terminate `scdaemon.exe` the same way.
- `ykman/_cli/otp.py:435-440` — `--upload` raises `CliFail` and tells the user to upload a CSV manually at `https://upload.yubico.com`. There is no HTTP client in this package.
- `ykman/settings.py:102-108` — OS keyring stores a local Fernet wrap key (`YKMAN_KEYRING_SERVICE` / `YKMAN_KEYRING_KEY`, default service `ykman`). Secrets stay in the local JSON store. No outbound call.
- `yubikit/piv.py:666-677` — `gzip.decompress` / `zlib.decompress` on a certificate the key returned, with a length check for the Net iD zlib framing.
- `yubikit/core/smartcard/scp.py:55` — `_DEFAULT_KEY = b"\x40\x41...\x4f"`, the published GlobalPlatform default key, used as an SCP parameter default.
- `ykman/hid/{windows,macos,freebsd}.py` and the matching `fido2/hid/*` modules — ctypes against `hid.dll`, `setupapi`, `kernel32`, `webauthn`, `user32` (all with `LOAD_LIBRARY_SEARCH_SYSTEM32`), IOKit, CoreFoundation, and libc. No other libraries are loaded.
- `fido2/ctap2/blob.py:45-50` — raw deflate for the CTAP large-blob extension, then AES-GCM.
- `fido2/mds3.py:495-526` — `parse_blob()` parses a caller-supplied MDS3 JWT. It does not download the blob. A `None` trust root skips signature verification and logs that the content is not verified; that is an explicit API choice.
- `fido2/rpid.py:43-57` — import-time read of the bundled public-suffix list. `urlparse` is used only to check RP ID against an origin. No socket.
- `cffi/setuptools_ext.py:16-26` and `cffi/_cffi_gen_src.py:51-53` — `compile`/`exec` of a build script the caller named (`cffi_modules` or `cffi-gen-src exec-python`). Not an install hook of cffi itself.
- `cffi/recompiler.py:80` and `:897-923` — `eval(self.flags, G_FLAGS)` where `flags` is a `'|'` join of `_CFFI_F_UNION`, `_CFFI_F_OPAQUE`, `_CFFI_F_CHECK_FIELDS`, `_CFFI_F_PACKED`, and `_CFFI_F_EXTERNAL`. `G_FLAGS` in `cffi_opcode.py:180` is those five integers.
- `cffi/api.py:770` — `compile(pysource, "cffi_init", "exec")` syntax-checks embedding init code before it is written into generated C. It does not run it.
- `cffi/verifier.py:151` — `__import__(self.ext_package)` to locate an already-built extension.
- `cffi/setup.py:126` — `os.popen('brew --prefix libffi')` only on macOS when Homebrew exists, to set `PKG_CONFIG_PATH`.
- `protobuf/setup.py:30` — `exec` of the local `google/protobuf/__init__.py` to read `__version__`.
- `google/protobuf/internal/api_implementation.py:40-65` — `importlib.import_module` of `google._upb._message` or `google.protobuf.pyext._message`, overridable by `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION`.
- `google/protobuf/descriptor_pb2.py` — the long `\x` blobs are generated `FileDescriptorProto` bytes passed to `AddSerializedFile`. Same pattern on the other `*_pb2.py` files.
- `lxml/ElementInclude.py:113-118` and `lxml/html/html5parser.py:229-230` and `lxml/html/__init__.py:1100-1120` — `urlopen` when the caller parses a URL or submits a form. Default SSL context; `verify=False` does not appear. `open_in_browser` (`html/__init__.py:1859-1879`) writes a temp file and opens `file://` in the local browser.
- Every `compile(` hit in yubikey-manager, fido2, and lxml is `re.compile`.

## Coverage and limits

Static review only. Nothing from these trees was executed, imported, installed, or built. No network lookups.

Pattern scan over every `.py`, `pyproject.toml`, `setup.py`, and `setup.cfg` in the five review trees: `exec`, `eval`, `compile`, `__import__`, `importlib`, `marshal`, `pickle`, `base64`, `zlib`, `subprocess`, `os.system`, `os.popen`, `ctypes`, `socket`, `urllib`/`urlopen`, `requests`, TLS-verify disables, `os.environ`/`getenv`, telemetry strings, URLs, IPv4-like tokens, long hex runs, and long base64-like runs.

Read in full, or the whole relevant function: yubikey-manager `pyproject.toml`, METADATA header, `script.py`, `settings.py`, `scripting.py` (module docstring and `ScriptingDevice`), `pcsc/__init__.py` connection and kill helpers, the OTP `yubiotp` command through the upload rejection, `logging.py`, `yubikit/logging.py`, both `__init__.py` version files, `piv.decompress_certificate`, SCP default key; fido2 `pyproject.toml`, METADATA header, `__init__.py`, `rpid.py`, `mds3.parse_blob`, `ctap2/blob.py` compress path, `hid/__init__.py`; cffi `setup.py`, `pyproject.toml`, `setup.cfg`, `__init__.py`, `setuptools_ext.py` through the exec helper, `_cffi_gen_src.py`, the recompiler flag builder, `cffi_opcode.G_FLAGS`, `api.embedding_init_code`, `verifier._locate_module`; protobuf `setup.py`, `setup.cfg`, `__init__.py`, `runtime_version.py`, `api_implementation.py`, `pyext/cpp_message.py`; lxml `setup.py`, `pyproject.toml`, `setup.cfg`, `__init__.py`, `tools/manylinux/build-wheels.sh`, the three `urlopen` call sites and `open_in_browser`.

Sampled rather than line-read: yubikey-manager CLI modules (`_cli/piv.py`, `oath.py`, `fido.py`, `otp.py`, `openpgp.py`, and the rest of the click commands) and the large `yubikit/{openpgp,piv,yubiotp,management}.py` protocol implementations, beyond the hits above; fido2 `webauthn.py`, `ctap2/*`, `attestation/*`, `cose.py`, `server.py`, `client/win_api.py` beyond the DLL load; cffi `api.py`, `cparser.py`, `backend_ctypes.py`, `vengine_cpy.py`, `vengine_gen.py`, `model.py`; protobuf `descriptor.py`, `text_format.py`, `json_format.py`, `internal/{decoder,encoder,python_message,containers}.py`, and the generated `*_pb2.py` bodies; lxml `html/__init__.py` outside the HTTP helpers, `html/_difflib.py` (vendored difflib), `doctestcompare.py`, `isoschematron/__init__.py`.

Not reviewed, because they are not in the extracted trees:

- All native code. cffi: 99 `_cffi_backend` binaries. protobuf: 6 `google/_upb/_message` binaries. lxml: 1135 extension modules. The representative-wheel RECORDs name the expected modules only. No disassembly, strings, or signature check.
- cffi C headers listed in RECORD (`_cffi_include.h`, `_embedding.h`, `parse_c_type.h`, `_cffi_errors.h`).
- `fido2/public_suffix_list.dat` (RECORD hash and size above).
- lxml Cython sources, libxml/libxslt/zlib headers, and ISO Schematron XSL/RNG shipped in the wheel RECORD.
- lxml’s static-dependency fetch script. Version pins are in `pyproject.toml`. Whether those downloads check a hash is not visible here.
- Sdist contents other than the extracted build scripts. TRIAGE already reports no Python drift between sdist and wheel.

No install-time network hook, obfuscated payload, hidden entry point, or `.pth` file showed up in what was present to read.
