💡agent-bootstrap 0.2.9 loaded.
I'll inventory provenance and the review layout first, then review each attested package statically.Provenance matches the attested set. I'll pull triage flags and install hooks across those packages, then read the network and auth code.The triage diffs are limited to charset-normalizer and pyscard. I'll read those, plus certifi, cryptography, and the HTTP/auth loaders.## Verdicts

| package | version | provenance | verdict | reason |
|---|---|---|---|---|
| anyio | 4.16.0 | attested 2/2 GitHub:agronholm/anyio:publish.yml | PASS | Local worker IPC only (pickle/subprocess). |
| certifi | 2026.10.23 | attested 2/2 GitHub:certifi/python-certifi:release.yml | PASS | 118 self-signed public roots; no private CA. |
| chardet | 7.6.0 | attested 4/4 GitHub:chardet/chardet:release.yml | PASS | Pure-Python wheel matches sdist; native wheels only inventoried. |
| charset-normalizer | 3.5.2 | attested 4/4 GitHub:jawah/charset_normalizer:cd.yml | REVIEW | Sole wheel/sdist Python delta is `__init__.py`; custom build hook was not in the extract. |
| click | 8.5.0 | attested 2/2 GitHub:pallets/click:publish.yaml | PASS | Win32 console ctypes and shell-completion subprocess. |
| cryptography | 50.0.2 | attested 4/4 GitHub:pyca/cryptography:pypi-publish.yml | PASS | Python matches sdist; `_rust.abi3.so` not disassembled. |
| filelock | 4.2.0 | attested 2/2 GitHub:tox-dev/filelock:release.yaml | PASS | `atexit` releases a lock. |
| google-api-core | 2.43.2 | attested 2/2 Google:None: | PASS | OpenTelemetry attribute helpers; no phone-home. |
| google-api-python-client | 2.201.0 | attested 2/2 Google:None: | PASS | Discovery client for Google API hosts. |
| google-auth | 2.62.0 | attested 2/2 Google:None: | PASS | Credential flows; `verify=False` is an explicit JWT API. |
| google-auth-httplib2 | 0.4.4 | attested 2/2 Google:None: | PASS | httplib2 transport adapter. |
| google-auth-oauthlib | 1.5.0 | attested 2/2 Google:None: | PASS | Localhost OAuth redirect listener. |
| googleapis-common-protos | 1.76.0 | attested 2/2 Google:None: | PASS | Generated protos; no pattern hits. |
| httplib2 | 0.32.1 | attested 2/2 GitHub:httplib2/httplib2:publish.yaml | PASS | TLS verification on unless the caller disables it. |
| idna | 3.20 | attested 2/2 GitHub:kjd/idna:deploy.yml | PASS | `re.compile` only. |
| jeepney | 0.9.0 | attested 2/2 GitLab:takluyver/jeepney: | PASS | Local D-Bus framing. |
| oauthlib | 4.0.1 | attested 2/2 GitHub:oauthlib/oauthlib:python-build.yml | PASS | Signing logic; `urllib.request` parses headers. |
| pathvalidate | 3.3.1 | attested 2/2 GitHub:thombashi/pathvalidate:release.yml | PASS | Path checks; `setup.py` `exec` reads `__version__.py`. |
| proto-plus | 1.29.0 | attested 2/2 Google:None: | PASS | Protobuf bytes use URL-safe base64. |
| pyscard | 2.3.2 | attested 3/4 GitHub:LudovicRousseau/pyscard:build.yml | PASS | Wheel-only `scard.py` is SWIG output; `_scard` extension not disassembled. |
| python-dateutil | 4.0.0 | attested 2/2 GitHub:dateutil/dateutil:publish.yml | PASS | Optional tz import. |
| requests | 2.34.2 | attested 2/2 GitHub:psf/requests:publish.yml | PASS | `Session.verify` defaults to True. |
| secretstorage | 3.5.0 | attested 2/2 GitHub:mitya57/secretstorage:main.yml | PASS | Secret Service over local D-Bus. |
| typing-extensions | 4.16.0 | attested 2/2 GitHub:python/typing_extensions:publish.yml | PASS | `eval` resolves annotations. |
| tzdata | 2026.6 | attested 2/2 GitHub:python/tzdata:publish.yml | PASS | IANA zone data; no pattern hits. |
| uritemplate | 4.2.0 | attested 2/2 GitHub:python-hyper/uritemplate:release.yml | PASS | `requests.get` is a docstring example. |
| urllib3 | 2.8.0 | attested 2/2 GitHub:urllib3/urllib3:publish.yml | PASS | Cert verification on; hostname check is moved, not dropped. |
| build | 1.6.1 | attested 2/2 GitHub:pypa/build:cd.yml | PASS | Subprocess runs the project's build backend. |
| hatchling | 1.29.0 | attested 2/2 GitHub:pypa/hatch:build-hatchling.yml | PASS | `eval` of a local version expression at build time. |
| packaging | 26.3 | attested 2/2 GitHub:pypa/packaging:publish.yml | PASS | manylinux probe via ctypes. |
| pathspec | 1.1.1 | attested 2/2 GitHub:cpburnz/python-pathspec:publish-to-pypi.yml | PASS | `re.compile`. |
| pip | 26.3 | attested 2/2 GitHub:pypa/pip:release.yml | PASS | Distlib launchers; TLS off only for trusted-host. |
| pluggy | 1.7.0 | attested 2/2 GitHub:pytest-dev/pluggy:deploy.yml | PASS | No pattern hits, no hooks. |
| pyproject-hooks | 1.3.3 | attested 2/2 GitHub:pypa/pyproject-hooks:ci.yml | PASS | Subprocess runner for backends. |
| staticx | 0.14.2 | attested 2/2 GitHub:JonathonReinhart/staticx:publish-pypi.yml | PASS | Bundled `libnssfix.so`; git describe only if `.git` exists. |
| trove-classifiers | 2026.9.21.13 | attested 2/2 GitHub:pypa/trove-classifiers:release.yml | PASS | Classifier list and CLI. |
| wheel | 0.48.0 | attested 2/2 GitHub:pypa/wheel:publish.yml | PASS | Mach-O parser; base64 decodes RECORD hashes. |

`modern-httplib2` was skipped. No in-scope package is FAIL.

Google packages are attested 2/2 with publisher `Google:None:` in `triage/prov-runtime.json`. The identity is Google's trusted publisher. The extract has empty repository and workflow fields. METADATA homepages are `googleapis` GitHub paths. That matches how these libraries are published. It is a weaker link to a named workflow than a GitHub OIDC attestation.

For chardet, charset-normalizer, cryptography, and pyscard, `attested N/N` is the checked sample (`checked` 4), not every wheel. chardet has 46 files, charset-normalizer 172, cryptography 59, pyscard 24.

## charset-normalizer 3.5.2 — REVIEW

METADATA author Ahmed R. TAHRI and `Project-URL: Code, https://github.com/jawah/charset_normalizer` match `GitHub:jawah/charset_normalizer:cd.yml`.

The wheel `__init__.py` was read in full. It re-exports the public API and attaches a `NullHandler`. No `exec`, network, or blob.

```45:48:review/runtime/charset-normalizer/WHEEL_charset_normalizer-3.5.2-py3-none-any/charset_normalizer/__init__.py
# Attach a NullHandler to the top level logger by default
# https://docs.python.org/3.3/howto/logging.html#configuring-logging-for-a-library

logging.getLogger("charset_normalizer").addHandler(logging.NullHandler())
```

Triage says this is the only Python file that differs from the sdist (`wheel_py_differs_from_sdist`: `charset_normalizer/__init__.py`, 2052 files compared). The sdist copy of that file is not in the review tree. The extracted sdist is only `setup.py`, `pyproject.toml`, `setup.cfg`, and `MANIFEST.in`.

`setup.py` Cythonizes `md` and `cd` only when `CHARSET_NORMALIZER_USE_CYTHON=1`. It does not rewrite `__init__.py`. The rewrite has to come from the custom backend declared here:

```1:4:review/runtime/charset-normalizer/SDIST_charset_normalizer-3.5.2/charset_normalizer-3.5.2/pyproject.toml
[build-system]
requires = ["setuptools>=68,<84.1"]
build-backend = "backend"
backend-path = ["_build_hook"]
```

`MANIFEST.in` includes `_build_hook/*.py`. Those files were not extracted, so the delta cannot be quoted. Confidence that the unread hook is malicious is low. A human should diff sdist `src/charset_normalizer/__init__.py` against the wheel and read `_build_hook`.

`cd.py` uses `importlib.import_module(f"encodings.{iana_name}")` to load stdlib codecs. Expected. Binary wheels add `charset_normalizer/cd.*.so` and `md.*.so` (341 binaries across wheels). The representative wheel is `py3-none-any` and has no extension. Those `.so` files were not disassembled.

## Network, TLS, and auth

**certifi.** `core.py` extracts `cacert.pem` via `importlib.resources` and registers `atexit` to close that context. Expected. The pem is in RECORD (`sha256` urlsafe `LvUq1WtIA-JkBFyRXlXCNsv6BFuEuB7-_CGKGetEvSs`, 235863 bytes) and was absent from the extracted tree. A local certifi 2026.10.23 file with that hash was parsed with OpenSSL: 118 certificates, every one self-signed with `CA:TRUE`. Names are public roots (ISRG, DigiCert, GTS Root R1/R3/R4, Amazon, and the rest of the Mozilla set). No private or test CA.

**requests.** `sessions.py:478` sets `self.verify = True`. `adapters.py:99` and `:344` set `cert_reqs = "CERT_NONE"` only on the `verify` false branch. `requests.get` / `requests.post` in `__init__.py:14` and `:23` are doctest lines. `packages.py:9` `__import__` is the vendored-dependency alias.

**urllib3.** `connection.py:1045-1056` sets `check_hostname = False` when urllib3 will check the hostname or fingerprint itself, or when pyOpenSSL cannot. `connection.py:1098-1101` still requires `verify_mode != ssl.CERT_NONE` before that match. Default verification stays on.

**httplib2.** `certs.py:27-38` uses `HTTPLIB2_CA_CERTS`, then `ca_certs_locater`, then certifi, then bundled `cacerts.txt`. `__init__.py:161` sets `CERT_NONE` only when `disable_ssl_certificate_validation` is true. The constructor default at `:1093` is `False`. `cacerts.txt` is in RECORD (135417 bytes) and was not on disk, so the fallback bundle was not parsed. With certifi installed, that file is unused.

**google-auth.** `jwt.py:35-37` documents `jwt.decode(encoded, verify=False)` as an optional skip. `_unverified_decode` (`jwt.py:133-171`) only splits and JSON-decodes. `verify=False` in `_client.py:376` and `:428` reads claims from an ID token the library just received. `pluggable.py` and `_cloud_sdk.py` run a caller-supplied executable or `gcloud`. `setup.py:96-98` does `exec` on `google/auth/version.py` to read `__version__`. Same version-file `exec` in `google-api-python-client` `setup.py:58-59` and `pathvalidate` `setup.py:28-29`.

**google-auth-oauthlib.** `flow.py:539-547` binds `localhost` and holds `::1` so another process cannot take the OAuth callback port. `interactive.py:45` probes a localhost port. Expected installed-app flow.

**google-api-core.** `_observability.py` builds OpenTelemetry span attributes. The triage hit `urllib.request` is a docstring at line 855. `timeout.py:27` `requests.get('https://example.com/...')` is a docstring.

**google-api-python-client.** `discovery.py` builds URLs under `https://www.googleapis.com/discovery/v1/apis/` and `https://{api}.googleapis.com/$discovery/rest`. `setup.py` version `exec` as above.

**oauthlib.** `oauth1/rfc5849/utils.py:8` imports `urllib.request` as `urllib2` and uses `parse_keqv_list` / `parse_http_list` (`utils.py:64-72`). No `urlopen`.

**secretstorage.** `__init__.py` opens a jeepney session-bus connection and exposes Secret Service collections. That is the library's purpose. No outbound HTTP.

**uritemplate.** `template.py:46-55` `requests.get` sits inside the `URITemplate` class docstring.

## Other packages with something to say

**pyscard.** `setup.py:73-83` runs SWIG during `build_py` (`BuildPyBuildExtFirst`) and exits if `swig` is missing. That is why `smartcard/scard/scard.py` is in the wheel and not the sdist. The wheel file starts `This file was automatically generated by SWIG` `Version 4.5.1` and imports `_scard` (`scard.py:109-113`). Every later call is an `SCard*` wrapper. No socket or HTTP. `_scard.*.so` / `.pyd` (23 binaries) were not disassembled. Provenance is 3 attested of 4 checked. Which of the four failed is not in the extract.

**cryptography.** Python compared to the sdist: 4524 files, no differences. `binding.py:14` loads `cryptography.hazmat.bindings._rust`. `cobblestone.py` re-exports `Cobblestone128/256` encryptors from that module. RECORD also lists `cryptography/hazmat/bindings/_rust/cobblestone.pyi`, so the name is a declared Rust module in this version. `_rust.abi3.so` is in RECORD at 14343432 bytes (`qdN5mVdXSAoxp-67-yIor5O-ze3SBeOvD2C6lkhlBAQ`) and was not in the extracted tree. Not disassembled. Sampled attestation is 4 of 59 artifacts.

**chardet.** Representative wheel is pure Python and matches the sdist. `models/__init__.py` zlib-decompresses local tables and checks `models.bin` with SHA-256 (`_V2_MAGIC = b"CMD2"`, `_ROWMAX_MAGIC = b"CRM1"`). RECORD lists `confusion.bin`, `idf.bin`, `models.bin` (588650 bytes), and `rowmax.bin`. Those files were not in the extract. Platform wheels add mypyc `.so` modules (900 binaries in the inventory). Not disassembled. METADATA author is Dan Blanchard and the homepage is `https://github.com/chardet/chardet`, matching the publisher. The Maintainer field says Ian Cordasco while Maintainer-email is Dan Blanchard's. That is a metadata slip on the canonical project.

**pip.** Six binaries, all `pip/_vendor/distlib/t32.exe`, `t64.exe`, `t64-arm.exe`, `w32.exe`, `w64.exe`, `w64-arm.exe`. Those are distlib's Windows script launchers. `InsecureHTTPAdapter.cert_verify` (`session.py:284-292`) forces `verify=False` and is mounted only for `trusted_hosts` (`session.py:405-406`). Vendored `pkg_resources` `exec` (`pkg_resources/__init__.py:1714` and `:1725`) runs entry-point scripts. Vendored pygments `exec` loads a user lexer file. No `.pth` in this wheel.

**staticx.** Binaries are `staticx/assets/debug/libnssfix.so` (17616 bytes) and `staticx/assets/release/libnssfix.so` (14424 bytes), the NSS helper this tool ships. `version.py:38-40` runs `git describe` only when `PROJPATH / '.git'` exists. An installed wheel has no `.git`, so it falls through to `importlib.metadata.version`.

**hatchling.** `hatchling/version/source/code.py:47-58` loads a path from the project being built and `eval`s the configured expression (default `__version__`) against that module's vars. Build-backend behavior, with the project's own source as input.

**typing-extensions.** `typing_extensions.py:4172` and `:4254` `eval` annotation strings and `ForwardRef` code objects in the caller's globals. The `exec` hit at `:1591` is a docstring sentence.

**filelock.** Publisher repo is `tox-dev/filelock`. METADATA homepage is `https://github.com/tox-dev/py-filelock`. Same org; the old repo name is still in the URL.

No in-scope package has a `.pth`, a non-empty `flags` list, or a `files_not_in_RECORD` hit. Entry points that exist are console scripts (`normalizer`, `chardetect`, `pip`, `wheel`, `staticx`, `trove-classifiers`, hatchling's build hook).

## Coverage and limits

Read in full: certifi `__init__.py` and `core.py`; charset-normalizer wheel `__init__.py`; cryptography `cobblestone.py` and `binding.py` through the loader; httplib2 `certs.py` and the SSL-context builder; google-auth `jwt.py` through `_unverified_decode`; google-api-core `_observability.py` through the gRPC hooks; uritemplate `template.py` through the class docstring; typing-extensions `eval` sites; secretstorage `__init__.py`; staticx `version.py`; hatchling `version/source/code.py`; pyscard `setup.py` through the extension declaration and the SWIG header plus the `_scard` import; the METADATA header of every package in the table.

Scanned every in-scope `.py` (wheels and extracted sdist scripts, tests skipped) for `exec(`, `eval(`, `os.system`, `marshal.loads`, `pickle.loads`, `b64decode`, `verify=False` / `CERT_NONE`, `__import__`, `ctypes`, `subprocess`, `socket.socket`, `urlopen`, `requests.get/post`, and `urllib.request`. Opened each remaining hit. Triage pattern lists and sdist-vs-wheel fields were read for every in-scope package.

Not read line by line: generated protobufs in googleapis-common-protos, most of oauthlib's RFC modules beyond the network/import scan, most of pip's vendored rich/pygments/urllib3 after the scan, cryptography's algorithm wrappers, and chardet's scoring pipeline past the model loader.

Could not inspect bytes: certifi `cacert.pem` was missing from the extract (audited via a hash-identical local copy, then deleted); httplib2 `cacerts.txt`; cryptography `_rust.abi3.so` and the `_rust/*.pyi` stubs; chardet `*.bin` and every mypyc `.so`; charset-normalizer `cd`/`md` `.so`; pyscard `_scard` extensions; staticx `libnssfix.so`; pip's six distlib `.exe` launchers. Those were inventoried from RECORD or TRIAGE only. charset-normalizer `_build_hook` and the sdist `__init__.py` were not in the review tree. Nothing was executed, imported, or installed. No network calls.

## Cleared

* certifi `atexit` and Google Trust Services roots R1/R3/R4: public Mozilla roots, self-signed.
* requests and urllib3 `CERT_NONE` / `check_hostname = False`: caller opt-out, or urllib3 doing its own hostname match.
* httplib2 `CERT_NONE`: only if `disable_ssl_certificate_validation` is true; default is false.
* google-auth `jwt.decode(..., verify=False)`, `subprocess` for `gcloud` and external-account executables, and `setup.py` `exec`: documented APIs and a version-file read.
* google-auth-oauthlib `socket` and `webbrowser`: localhost OAuth callback.
* google-api-core `urllib.request` and `requests.get`: docstring text.
* uritemplate `requests.get`: docstring example.
* oauthlib `import urllib.request`: `parse_http_list` / `parse_keqv_list`.
* typing-extensions `eval` / `exec`: annotation evaluation; the `exec` match is prose.
* hatchling `eval`: version expression from the tree being built.
* anyio `pickle.loads` and `exec`: worker processes the library starts.
* pip `verify=False`: `InsecureHTTPAdapter` mounted for trusted hosts. Distlib `.exe` files are the usual launchers. Vendored `pkg_resources` / pygments `exec` loads entry points and custom formatters.
* staticx `git` subprocess: runs only when a `.git` directory sits next to the package.
* click ctypes: Windows console. packaging / wheel ctypes: ELF/Mach-O tag parsing.
* pathvalidate and google client `setup.py` `exec`: reads `__version__`.
* pyscard wheel-only `scard.py`: SWIG 4.5.1 output of the sdist build.
* secretstorage talking to the secret service: the package's job, over local D-Bus.
* filelock homepage `py-filelock` versus publisher `tox-dev/filelock`: same organization.
* chardet Maintainer name versus email: canonical `chardet/chardet` publisher, author Dan Blanchard.
