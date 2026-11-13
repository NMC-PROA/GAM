💡agent-bootstrap 0.2.9 loaded.
Starting a static supply-chain review of `modern-httplib2` 1.32.1.post1: inventory the git tag and any PyPI artifacts, then read the HTTP, TLS, cache, and patch paths line by line. No install, import, or network.## Verdict

| Artifact | Verdict |
|---|---|
| Git source snapshot at `repos/modern-httplib2` (claimed tag `v1.32.1-1`, version string `1.32.1-1`) | **PASS** |
| PyPI wheel `modern_httplib2-*.whl` | **Not reviewed.** `artifacts-pypi/` does not exist. |
| PyPI sdist `modern_httplib2-*.tar.gz` | **Not reviewed.** Same. No wheel-versus-tag diff was possible. |

No malware indicator in the source tree. Nothing sends OAuth material, headers, or bodies to a host other than the request target or the caller-configured proxy. TLS verification is on unless the caller sets the historical httplib2 flag. There is no install hook, no obfuscated payload, and no dynamic execution of remote content.

`1.32.1-1` in `pyproject.toml` and `__version__` is the setuptools form of PEP 440 `1.32.1.post1`. Those two strings match each other.

## What I covered

Static read only. The package was not imported, installed, built, or executed, and nothing was fetched over the network.

Line-by-line: `modern_httplib2/__init__.py` (2829 lines), `auth.py`, `auto.py`, `certs.py`, `decode.py`, `error.py`, `iri2uri.py`, `patch.py`, plus `pyproject.toml`, both GitHub workflows, and `README.md`.

`benchmark.py` was read through the live URL list, the site-packages loader, and the subprocess probe. Tests were searched in full. Read in detail: `conftest.py`, `tests/__init__.py` server helper, `test_patch.py`, `test_security.py` (TLS, redirects, cache names), `test_modern_features.py` (token debug, HTTP/2 downgrade), and the small fuzz/SOCKS files. The upstream-style suites (`test_http.py`, `test_cache.py`, `test_auth.py`, `test_proxy.py`, `test_https.py`, `test_encoding.py`, `test_other.py`, `test_uri.py`) were pattern-scanned, not re-read assertion by assertion.

No `.so`, `.whl`, `.pth`, `setup.py`, or `setup.cfg`. No non-ASCII in `modern_httplib2/`.

## What I could not do

- Confirm commit `1fac2e5d` or tag `v1.32.1-1`. This directory has no `.git`.
- Diff a wheel or sdist against the tree.
- Audit `httpx`, `httpcore`, `h2`, `certifi`, `pyparsing`, or `PySocks` themselves. They are declared, not vendored.
- Byte-compare this tree with upstream `httplib2`. Behavior below is judged against the httplib2 API this package claims to keep.

## Where a bearer token goes

`Http.request` normalizes the caller URI and opens a connection to that authority only (`__init__.py` 2535–2623). The connection class builds an `httpcore` request whose scheme, host, and port are `self`, and whose target is the path (`1899–1930`). The only `socket.connect` is in `_connect_raw_socket` (`1739–1817`): either the target or a `ProxyInfo` host. `import httpx` at line 91 is unused. No `httpx.Client` is constructed, so there is no second client with its own default destination.

Default redirect policy drops `Authorization` (`2488–2489`). An HTTPS-to-HTTP redirect drops it even when `forward_authorization_headers` is True (`2504–2511`). Cross-authority redirects also drop `Cookie` and `Host` (`2512–2516`).

## TLS and CA source

```275:303:repos/modern-httplib2/modern_httplib2/__init__.py
def _build_ssl_context(
    disable_ssl_certificate_validation,
    ...
):
    context = ssl.SSLContext(DEFAULT_TLS_VERSION)
    context.check_hostname = not disable_ssl_certificate_validation
    context.verify_mode = ssl.CERT_NONE if disable_ssl_certificate_validation else ssl.CERT_REQUIRED
    ...
    if not disable_ssl_certificate_validation:
        context.load_verify_locations(ca_certs)
```

`disable_ssl_certificate_validation` defaults to False (`2165`, `2014`). `CERT_NONE` is only that explicit httplib2 switch. `load_verify_locations` is called alone, so a custom bundle replaces the trust store rather than being merged with it. `load_default_certs` is not called. HTTP/2 fallback (`2076–2092`) keeps that same context and only sets ALPN to `http/1.1`. Certificate and hostname failures are excluded from fallback (`897–926`).

`certs.py` bundles no PEM. `where()` order is: `HTTPLIB2_CA_CERTS` if that path is a file, else `ca_certs_locater.get` if that module is already installed, else `certifi.where()`. `CA_CERTS = certs.where()` runs at import (`__init__.py` 261). An explicit `ca_certs=` argument wins (`264–269`).

## Monkeypatch (`auto.py`, `patch.py`)

`import modern_httplib2` does not patch anything. `import modern_httplib2.auto` calls `patch()` (`auto.py` 3–5).

`patch()` (`patch.py` 93–131) does four things:

- `sys.modules["httplib2"]` and `httplib2.{auth,certs,decode,error,iri2uri}` point at this package.
- `importlib.metadata.version` is wrapped so the names `httplib2` and `modern-httplib2` return `modern_httplib2.__version__` (`65–78`). Other distribution names go to the original function.
- If `gam` or `__main__` is already loaded and has `lib_version`, that attribute is replaced with the wrapped `version` function (`80–83`).
- A `sys.meta_path` finder runs only for `glverlibs` or `*.glverlibs`, then rewrites the string `httplib2` inside `GAM_VER_LIBS` to `modern-httplib2` (`13–62`, `123–131`).

That is the documented GAM compatibility shim. It does not wrap `requests`, `urllib`, `httpx`, `ssl`, or socket. It does not add a proxy or a destination.

## Dependencies and install hooks

`pyproject.toml` 15–19, from PyPI names only, no URL, git, or extra index:

- `pyparsing>=3.0.0` (WWW-Authenticate parsing in `auth.py`)
- `httpx[http2]>=0.28.0` (brings `httpcore`, `h2`, `h11`)
- `certifi>=2026.10.19`
- optional `PySocks>=1.7.1`

No `[project.scripts]` or entry points. Build backend is `setuptools.build_meta`. Package discovery is `modern_httplib2*` only, so tests and `benchmark.py` stay out of the wheel. No `setup.py` and no `.pth`.

Environment variables read by the library are all HTTP-related: `HTTPLIB2_CA_CERTS`, `MODERN_HTTPLIB2_ENABLE_HTTP2`, `HTTPLIB2_ENABLE_HTTP2`, `MODERN_HTTPLIB2_AUTO_DOWNGRADE`, `HTTPLIB2_AUTO_DOWNGRADE`, `http_proxy` / `HTTP_PROXY`, `https_proxy` / `HTTPS_PROXY`, `no_proxy` / `NO_PROXY`, and `httplib2_decode_limit_{hard,safe,ratio,chunk}` (either case). No credential-file or cloud-metadata paths.

## Cleared

- **`base64` and `zlib`.** `base64.b64encode` builds the Basic `Authorization` value (`602–603`). `zlib` is the gzip/deflate body decoder (`decode.py`). No `b64decode`, `marshal`, `pickle`, `eval`, `exec`, or `__import__` in the library. Pickle appears only in `tests/test_other.py` round-trips.
- **Debug printing of headers, bodies, and `proxy_pass`.** Gated on `debuglevel > 0`. The module default is `0` (`144`) and no environment variable turns it on. `_debug_print` (`147–158`) forwards to a caller-installed `print` (the GAM redaction hook exercised in `tests/test_modern_features.py` 432–488). With the default printer, a debug session would show bearer tokens and the proxy password (`1791–1792`, `1943–1950`). That is opt-in stdout, the same class as httplib2 debug.
- **File cache.** `FileCache` (`670–696`) writes under the directory the caller passed. `_updateCache` (`497–531`) stores the response and, when `Vary` names a request header, that request header. Nothing is written if `cache` is unset. `safename` strips path separators.
- **HTTP/2 to HTTP/1.1 fallback.** On a transport reset, `_conn_request` (`2365–2383`) records that host and retries on the same connection object. The TLS context is kept. The retry does not change scheme or host.
- **`ca_certs_locater`.** Optional import (`certs.py` 13–19), not a declared dependency, so this package does not install it. If some other package has already installed that module, its `get()` can choose the default CA file. That is the historical httplib2 hook. An explicit `ca_certs=` bypasses it.
- **Test certificates.** `tests/tls/` holds a self-signed `CN=httplib2-test-CA`, `C=ZZ`, issued 2025-07-23, plus localhost server and client certs. The library never loads that directory. `tests/` is outside the wheel package set.
- **`benchmark.py`.** A manual script. When run, it GETs public keyless URLs (`versionhistory.googleapis.com`, `www.googleapis.com/oauth2/v3/certs`, `accounts.google.com/.well-known/openid-configuration`, `discovery.googleapis.com`, `storage.googleapis.com`, `www.cloudflare.com/cdn-cgi/trace`, `api.cdnjs.com`). The subprocess at `704` re-invokes that same local script. It is not an entry point and is not imported by `modern_httplib2`.
- **Publish workflow.** `publish.yml` uses PyPI Trusted Publishing (OIDC) and `actions/attest-build-provenance@v2`. Action tags are floating majors (`checkout@v4`, `setup-python@v5`, `pypa/gh-action-pypi-publish@release/v1`), and `pip install` is not hash-pinned. That is a reproducibility limit of the publisher workflow. There is no `curl | bash`, no extra host, and no TLS-verify disable. It did not change the PASS verdict.
- **Proxy defaults.** `Http()` reads `http_proxy` / `https_proxy` through `proxy_info_from_environment` (`802–811`). Unknown schemes are treated as an HTTP proxy. If a proxy is requested and PySocks is missing, it raises `ProxiesUnavailableError` (`1741–1742`) instead of connecting direct. `proxy_headers` is stored and debug-printed and is not attached to the socket.

## Source hashes (SHA-256)

Use these against the wheel and sdist `.py` files when they show up.

| File | SHA-256 |
|---|---|
| `modern_httplib2/__init__.py` | `e50ea05eb85a9755cdef6ba0111b5b80c2e2466a3933a659b5b90bdc03b0de7e` |
| `modern_httplib2/auth.py` | `6f0d70393d1c6e29561ac375300ba977d9a94bf4bcbcb0e5f2f80aacf747d26d` |
| `modern_httplib2/auto.py` | `0c6dfe8a564446f8dfc53ebe81a26748f33c877644a5c1d1c1650d17cb75561d` |
| `modern_httplib2/certs.py` | `7237b2c395898882cd6af9d4158ddf8c22f5c89f3dc601c045529b43ae814662` |
| `modern_httplib2/decode.py` | `bc962f86045489760c016d01f69ef5ce2a3ea60efa78a14cbaeb86e6e49e4157` |
| `modern_httplib2/error.py` | `840642b468aea7273f9802ca1186100da5dd80012d9f87c2b818208cd7ff7711` |
| `modern_httplib2/iri2uri.py` | `458dd3ec9df8dfed362c620cbbaacbab0e48bef451dcea68fd6e9e55d506eed4` |
| `modern_httplib2/patch.py` | `e3a486bf48e0fe698e535e0e829976819a7f27e8e9b5052681ec2c4043564067` |
| `pyproject.toml` | `df82b95cd4562f8250c1fb656b2dae3e88db5ed32c8d3964edd146b14fe35dc2` |
