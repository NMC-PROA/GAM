💡agent-bootstrap 0.2.9 loaded. I'll review the pinned runtime artifacts statically: provenance first, then install hooks and the credential-handling packages.The assignment is the unattested set: HTTP stack, OAuth, keyring, and passlib first. I'll pull provenance and triage flags before reading any code.Triage is clean of binaries and wheel/sdist diffs. Next I’ll read the install hooks and every credential or network hit in source.All 25 packages are **PASS**. None of the pinned wheels shows a malware or supply-chain backdoor. Every one of them is **unattested** (PyPI account only).

| Package | Version | Provenance | Verdict | Reason |
|---|---|---|---|---|
| httpx | 0.28.1 | 0/2, no attestation | PASS | HTTP client; TLS verify defaults on; no phone-home |
| httpcore | 1.0.9 | 0/2, no attestation | PASS | Caller-supplied connections only; default SSL uses certifi |
| h11 | 0.16.0 | 0/2, no attestation | PASS | Pure HTTP/1.1 state machine; no sockets |
| h2 | 4.4.1 | 0/2, no attestation | PASS | Pure HTTP/2 state machine; base64 is the HTTP2-Settings header |
| hpack | 4.2.0 | 0/2, no attestation | PASS | Static HPACK/Huffman tables; no I/O |
| hyperframe | 6.1.0 | 0/2, no attestation | PASS | Frame codec only |
| requests-oauthlib | 2.0.0 | 0/2, no attestation | PASS | Tokens go only to the caller’s token URL |
| pysocks | 1.7.1 | 0/3, no attestation | PASS | SOCKS client; proxy monkeypatch is opt-in |
| arrow | 1.4.0 | 0/2, no attestation | PASS | Date parser; `compile` hits are `re.compile` |
| python-pskc | 1.4 | 0/2, no attestation | PASS | Local PSKC XML; base64 is key material, not a loader |
| passlib | 1.7.4 | 0/2, no attestation | PASS | Local password hashes; generated `eval` is a PBKDF2 loop |
| distro | 1.9.0 | 0/2, no attestation | PASS | Fixed `lsb_release` / `uname` / `oslevel` argv |
| importlib-metadata | 10.1.0 | 0/2, no attestation | PASS | Entry-point loader for installed distributions |
| zipp | 4.1.2 | 0/2, no attestation | PASS | Zipfile wrapper; imports stdlib `zipfile` |
| jaraco.classes | 3.4.0 | 0/2, no attestation | PASS | Class helpers; no I/O |
| jaraco-context | 6.1.2 | 0/2, no attestation | PASS | Download/clone helpers run only when called |
| jaraco-functools | 4.6.0 | 0/2, no attestation | PASS | `eval` is the documented `except_(use=...)` hook |
| more-itertools | 11.2.1 | 0/2, no attestation | PASS | Lazy `concurrent.futures` import |
| backports-tarfile | 1.2.0 | 0/2, no attestation | PASS | Stdlib tarfile backport with `data_filter`; no network |
| opentelemetry-api | 1.45.2 | 0/2, no attestation | PASS | No-op API; `requests.get` is a docstring example |
| keyring | 25.7.0 | 0/2, no attestation | PASS | OS keychain backends; no secret upload |
| pyasn1 | 0.6.5 | 0/2, no attestation | PASS | ASN.1 codecs; hex blobs are docstring examples |
| pyasn1-modules | 0.4.2 | 0/2, no attestation | PASS | RFC OID modules; PEM base64 decode of caller data |
| pyparsing | 3.3.3 | 0/2, no attestation | PASS | Parser; `eval` is inside a docstring |
| pycparser | 3.12 | 0/2, no attestation | PASS | C parser; `cpp` runs only from `preprocess_file` |

Names, authors, and homepage URLs match the known projects (Encode, python-hyper, requests, Anorov, arrow-py, Arthur de Jong, Eli Collins, python-distro, CPython/jaraco, OpenTelemetry, pyasn1, Paul McGuire, Eli Bendersky). No typosquat, no `.pth`, no binaries, no install-time network. Where triage compared wheel to sdist, `wheel_py_differs_from_sdist` and `wheel_py_not_in_sdist` were empty.

## Notes

**httpx / httpcore.** `create_ssl_context` uses certifi when `verify` is true. `CERT_NONE` is only the `verify=False` branch (`httpx/_config.py:41-44`). The CLI `--no-verify` flag defaults `verify` to true (`httpx/_main.py:416-421`). User-Agent is `python-httpx/{version}`. Basic and Digest auth attach credentials to the request the caller built. httpcore connects to the host it is given (`httpcore/_backends/sync.py:208-216`); `default_ssl_context` loads certifi.

**requests-oauthlib.** `fetch_token` refuses non-HTTPS token URLs, then `self.request`s that URL (`oauth2_session.py:267-390`). Compliance hooks start empty. `setup.py:26-28` runs `os.system("python setup.py sdist upload")` only when the last argument is `publish`. That file is not in the wheel.

**keyring.** Passwords stay in the selected backend. macOS loads `Security`, `CoreServices`, and `Foundation` via `ctypes.util.find_library` (`backends/macOS/api.py:25-27`). `urlopen` in `keyring/http.py` is a usage comment. `__import__` loads a backend class named by config or `PYTHON_KEYRING_BACKEND` (`core.py:133-135`). `keyring-path` in the user’s config is inserted on `sys.path` (`core.py:196-200`); that is the documented plugin path, and nothing in this wheel sets it.

**passlib.** `crypto/digest.py:977-1000` builds a PBKDF2 xor loop from the digest size and `compile`/`eval`s that local string. The scrypt “ctypes” hit is a docstring; the loader imports the optional `scrypt` package. The wheel ships `passlib/tests/`; nothing imports them at startup. `setup.py` leaves `cmdclass` empty, and the Mercurial stamp block is behind `stamp_build = False`.

**python-pskc.** Decryption stays in-process (`pskc/encryption.py`). `http://www.w3.org/...` strings are XML encryption identifiers. `setup.py:33-34` runs `chmod` only when `sdist` is in `argv`.

**jaraco.context.** `tarball()` downloads a URL and extracts it (`jaraco/context/__init__.py:105-107`). `repo_context()` runs `git` or `hg clone` (`254-259`). Neither runs at import. `tarfile.data_filter` is composed into the extract filter.

**backports-tarfile.** The sdist tree is `review/runtime/backports-tarfile/` (pyproject only). The wheel is `review/runtime/backports.tarfile/`. Triage compared 0 files, so there is no sdist-vs-wheel diff. The wheel’s `data_filter` rejects absolute links and link targets outside the destination (`backports/tarfile/__init__.py:807-835`). `backports/__init__.py` is `pkgutil.extend_path`.

**opentelemetry-api.** Entry points in the wheel point at in-package no-op providers. `requests.get("http://scrapethis.com")` is inside a docstring (`metrics/_internal/__init__.py:436-446`). `subprocess` in `_envcarrier.py` is a comment about passing an env dict to the caller’s `subprocess.run`.

**pyparsing.** `results.py:66` `eval` is in a docstring example. `show_best_practices()` prints a bundled Markdown file or an in-module fallback (`pyparsing/__init__.py:206-237`). It is not called on import.

## Coverage and limits

Static reading and search only. Nothing was executed, imported, installed, or built. No network lookups, so versions were not byte-compared to GitHub.

Read in full or nearly in full: httpx `_auth.py`, `_config.py`, `__init__.py`, CLI `main`; httpcore `_ssl.py` and sync `connect_tcp`; requests-oauthlib `setup.py`, `__init__.py`, `oauth2_auth.py`, and the token-fetch path; keyring `core.py`, `http.py`, `devpi_client.py`, macOS ctypes preamble, chainer; passlib `setup.py`, `__init__.py`, the PBKDF2 generator, scrypt backend loader; jaraco.context and the `eval` in jaraco.functools; pysocks proxy setup; pycparser `preprocess_file`; distro’s subprocess commands; h11/h2/hpack/hyperframe package inits; python-pskc `__init__.py` and the start of `encryption.py`; pyasn1-modules `pem.py`; otel metrics docstring; backports tarfile filter and CLI `main`.

Every `.py`, `setup.py`, and `pyproject.toml` under these packages was searched for `exec`, `eval`, `compile`, `__import__`, `base64`, `marshal`, `pickle`, `subprocess`, `os.system`, `socket`, `urlopen`, `ctypes`, TLS verification switched off, and hardcoded IPs. Triage pattern hits were opened. Build backends are hatchling, setuptools, or flit. No `.pth`, no extension modules, no console entry point outside the package.

Not line-read: httpx `_client.py` (about 2k lines) and the async twins of httpcore; hpack `huffman_table.py` (169 KB static table; header identifies the nghttp2 source); h2 `connection.py` / `stream.py` beyond the settings-header base64; pyparsing `core.py` (253 KB); pycparser `c_parser.py`; pyasn1 codec modules and the 132 `pyasn1_modules` RFC files past `pem.py`; most passlib hash handlers; backports `tarfile/__init__.py` past the filter and CLI (108 KB). `pyparsing/ai/best_practices.md`, `py.typed`, and license files are in RECORD and absent from this extract, so that Markdown was not read. PySocks provenance lists 3 artifacts; only the pure-Python wheel was in the tree.

## Cleared

- httpx `CERT_NONE` and CLI `--no-verify`: verification stays on unless the caller sets `verify=False`.
- httpx `b64encode`: HTTP Basic credentials on the outgoing request.
- httpx / h11 / arrow / importlib-metadata `compile(`: `re.compile`.
- h11 `setup.py` `exec(open("h11/_version.py"))`: local version read at build time.
- h2 `urlsafe_b64encode`: HTTP/2 connection-upgrade settings header (`connection.py:586-592`).
- requests-oauthlib `sdist upload`: maintainer `setup.py publish` shortcut, not an install hook.
- python-pskc `chmod -R a+rX`: only while building an sdist.
- passlib `eval`: generated local PBKDF2 helper, not an external payload.
- passlib test `subprocess`: `htpasswd` from the test suite, not imported by `passlib/__init__.py`.
- PySocks `module.socket.socket = socksocket`: `wrap_module()`, and it refuses to run without a default proxy (`socks.py:139-148`).
- jaraco.context `__import__('pytest')`: inside a docstring.
- jaraco.functools `eval(use)`: caller-supplied expression for `except_`.
- more-itertools `__import__('concurrent.futures')`: lazy import.
- zipp `importlib.import_module('zipfile')`: stdlib overlay.
- importlib-metadata `import_module`: `EntryPoint.load()`.
- opentelemetry `requests.get`: docstring example, not a call.
- keyring `urlopen`: module docstring.
- pyparsing `eval(s)`: docstring example.
- pyparsing “AI INSTRUCTIONS”: text printed only if `show_best_practices()` is called.
- pyasn1 `\xNN` sequences: DER examples in docstrings.
- distro `check_output("oslevel")`: fixed program name, `shell` left false.
- pycparser `check_output`: `cpp` argument list from `preprocess_file`.
- h2 sdist `tests/h2spectest.sh`: tox helper, not in the wheel and not an install script.

**VERDICT:** PASS for all 25 artifacts. No malicious indicator found in the code that was read or in the pattern scan. Residual risk is the missing PEP 740 attestation and the large files that were searched rather than read line by line.
