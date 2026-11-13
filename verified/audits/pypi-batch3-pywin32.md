💡agent-bootstrap 0.2.9 loaded.
I'll review pywin32 and pywin32-ctypes statically: provenance, install hooks, pattern hits, and anything outside the normal Windows layout. No execution, imports, or network calls.The `.pth` imports `pywin32_bootstrap` at startup, and both packages lack PEP 740 attestations. I'll read those hooks and scan for exfil, dynamic exec, and unexpected binaries.| Package | Version | Provenance | Verdict | Reason |
|---|---|---|---|---|
| pywin32 | 312 | attested 0/3; homepage `https://github.com/mhammond/pywin32`; uploaded 2026-06-04 | **PASS** | Install hooks and Python sources match the Mark Hammond Windows-extension tree. No exfil, remote fetch, or extra top-level code. Native binaries inventoried only. |
| pywin32-ctypes | 0.2.3 | attested 0/2; homepage `https://github.com/enthought/pywin32-ctypes`; uploaded 2024-08-14 | **PASS** | Pure-Python ctypes/cffi wrappers of `kernel32` and `advapi32`. Wheel Python matches the sdist (34 files). No install hook and no network code. |

## pywin32 312

Identity matches the long-running project: Author Mark Hammond, `mhammond@skippinet.com.au`, PSF license, Project-URLs all under `github.com/mhammond/pywin32` and `mhammond.github.io`. `METADATA` describes a manual `twine upload` of GitHub Actions wheels, which is consistent with attested 0/3 (maintainer PyPI account only). No `Requires-Dist`. Wheel tag `cp310-cp310-win32`, generator setuptools 82.0.1.

`TRIAGE.json` lists `sdists: []` and `compared: 0`. The 451 `wheel_py_not_in_sdist` names are the whole Python tree with nothing to diff against. Every file on disk is in `RECORD` (0 extras). The extract is a subset of `RECORD`: the non-Python members are absent here.

**Install-time surface (read in full).**

`pywin32.pth` adds `win32`, `win32\lib`, and `pythonwin`, then imports the bootstrap:

```7:7:review/runtime/pywin32/WHEEL_pywin32-312-cp310-cp310-win32/pywin32.pth
import pywin32_bootstrap
```

`win32/lib/pywin32_bootstrap.py` (26 lines) only calls `os.add_dll_directory` on the `pywin32_system32` package path. No network, no exec.

Entry points:

```1:3:review/runtime/pywin32/WHEEL_pywin32-312-cp310-cp310-win32/pywin32-312.dist-info/entry_points.txt
[console_scripts]
pywin32_postinstall = win32.scripts.pywin32_postinstall:main
pywin32_testall = win32.scripts.pywin32_testall:main
```

`pywin32-312.data/scripts/pywin32_postinstall.py` and `pywin32_testall.py` are byte-identical to `win32/scripts/` copies. Neither runs on import. `postinstall` runs only for `-install` / `-remove`. It copies `pywin32_system32\*.*` onto the Windows system directory (or `sys.prefix` if access is denied), registers three sample COM classes, writes Pythonwin file-association keys, and creates Start Menu shortcuts. That is the documented global install. It does not download anything. `testall` only `subprocess.run`s local test scripts when invoked.

**Layout.** Top-level names in `RECORD` are the usual set: `pythoncom.py`, `pywin32.pth`, `pywin32.version.txt`, `PyWin32.chm`, `pywin32_system32/`, `adodbapi/`, `isapi/`, `pythonwin/`, `win32/`, `win32com/`, `win32comext/`. `pythoncom.py` and `win32/lib/pywintypes.py` only load the matching `pythoncom310.dll` / `pywintypes310.dll` via `importlib` extension loaders.

**Binaries (inventory only).** Representative wheel `RECORD` lists 57 PE files: 50 `.pyd`, 5 `.dll`, 2 `.exe`. Names are the usual ones (`pythoncom310.dll`, `pywintypes310.dll`, `Pythonwin.exe`, `pythonservice.exe`, `scintilla.dll`, `PyISAPI_loader.dll`, `perfmondata.dll`, `win32*.pyd`, and the `win32comext` extension `.pyd`s). `TRIAGE.json` `n_binaries_all_wheels` is 1197 across 21 wheels, which matches about 57 binaries times 21. The triage sample of 25 (sizes and 16-hex SHA-256 prefixes) is the same name set. None of those files are in the extracted tree, so they were not disassembled.

**Pattern hits.** All 72 triage hits are in IDE, COM, demo, test, or header-translation code. Library `exec`/`eval` is the COM dynamic dispatcher (`win32com/client/dynamic.py:412-418`), the Active Scripting host (`win32comext/axscript/client/framework.py:1114-1176`), the axdebug expression evaluator, and the sample `Python.Interpreter` COM server (`win32com/servers/interp.py:40` and `:48`). `isapi/install.py:345` is `eval("_AssignScriptMaps" + update.capitalize())` against three local functions. `gencache.py` pickles a local `dicts.dat` typelib index; no pickle is shipped. `pythonwin/pywin/scintilla/config.py:104-117` `marshal.load`s a local `.cfc` cache of the editor config. URLs in sources are comments or demos (GitHub, Microsoft docs, `python.org`, archive.org). No base64 blobs, no long lines, no TLS-verification disable, no pastebin/webhook/raw-GitHub fetch.

## pywin32-ctypes 0.2.3

Identity matches Enthought’s partial pywin32 reimplementation: summary and homepage in `METADATA` and `setup.cfg`, BSD-3-Clause, `Requires-Python: >=3.6`, no dependencies. Pure wheel `py3-none-any`, generator `bdist_wheel (0.36.2)`. Attested 0/2.

`Author-email: info@enthough.com` (missing `t`) is in both `setup.cfg` and wheel `METADATA`. The code never uses that address. Homepage is `https://github.com/enthought/pywin32-ctypes`.

**Build.** Sdist `setup.py` reads `VERSION` and writes `win32ctypes/version.py`, then calls `setup()`. The installed file is `__version__ = "0.2.3"`. Triage: 34 Python files compared, `wheel_py_differs_from_sdist` empty, `wheel_py_not_in_sdist` empty. No `.pth`, no entry points, no data scripts, no binaries. `RECORD` matches the tree; the only unhashed row is `RECORD` itself.

**Runtime.** `win32ctypes/core/__init__.py` installs a `MetaPathFinder` that redirects `win32ctypes.core._dll` and six siblings to the cffi backend if `cffi` imports, otherwise ctypes. `importlib.import_module` targets only those in-package names. DLL loads are `dlls.kernel32` and `dlls.advapi32` (`WinDLL` / `ffi.dlopen('{}.dll')`). Public API is resource and library load/update, `GetTickCount`, Windows/System directory, and `CredRead` / `CredWrite` / `CredDelete` / `CredEnumerate` against the local Windows credential store. Nothing in the package opens a socket or URL. Tests talk to the local credential manager with a fake target `jone@doe` and only run under unittest.

## Coverage and limits

Read in full: `pywin32.pth`, `pywin32_bootstrap.py`, both copies of `pywin32_postinstall.py` and `pywin32_testall.py`, `pythoncom.py`, `pywintypes.py`, `METADATA`, `WHEEL`, `entry_points.txt`, `top_level.txt`, and the install/eval regions cited above. Scanned every `.py` in the pywin32 extract for `exec`/`eval`/`compile`/`__import__`, subprocess, `os.system`, sockets, URLs, IPs, pickle/marshal/base64/zlib, and high-entropy lines. Did not read every line of `win32con.py`, `winerror.py`, `win32cryptcon.py`, demos, or the Pythonwin IDE.

pywin32-ctypes: read the sdist build files, metadata, backend loader, both DLL/util modules, authentication, resource bindings, public `win32api`/`win32cred`/`pywintypes` facades, and tests. `cffi/_resource.py` was checked through its `kernel32` bindings and the matching ctypes module, which was read through the callback wrappers.

Not reviewed as code: pywin32’s 57 PE files per wheel (and the other 20 wheels), `PyWin32.chm`, HTML/HTM help, `.gif`/`.bmp`, `win32/include` headers, `.lib` import libs, and the `.vbs`/`.js`/`.asp`/`.sct` test files. They are named in `RECORD` and missing from this extract. No byte comparison to the GitHub tag was possible (no sdist for pywin32, no PEP 740 attestation for either package, and this review made no network calls).

## Cleared

- **`pywin32.pth` + `pywin32_bootstrap.py`.** Startup import only adds the DLL directory. Expected for a portable install where postinstall was not run.
- **`pywin32_postinstall.py` copying DLLs to System32 and registering COM servers** (`com_modules` at lines 47-52, `RegisterCOMObjects` at 211-227, copy loop at 408-422). Documented global install. The COM classes are the usual samples: `Interpreter`, `DictionaryPolicy`, `PyScript`. `Interpreter.Eval`/`Exec` run only when a COM client calls them.
- **`win32com/client/dynamic.py:412` `compile` + `:418` `exec`.** Builds a Python method from a COM type-library signature at call time.
- **`win32com/client/gencache.py:86` and `:130` pickle of `dicts.dat`.** Local generated-typelib index. No pickle payload is in the wheel.
- **`pythonwin/.../scintilla/config.py:104` `marshal.load`.** Cache of a local editor `.cfg`, checked against mtime, size, and `MAGIC_NUMBER`.
- **`win32/scripts/h2py.py:152` `exec`.** Vendored CPython header-to-Python tool. Runs only as a script; the statement is a `#define` turned into an assignment.
- **`win32/lib/win32serviceutil.py:801` `os.system`.** Debug-launch of the already-installed service exe (`LocateSpecificServiceExe`) when the user passes `debug`.
- **`isapi/install.py:345` `eval`.** Selects `_AssignScriptMapsReplace` / `End` / `Start` from the `ScriptMapUpdate` string.
- **`adodbapi/test/test_adodbapi_dbapi20.py:35-40`.** Test-only SQL target `testsql.2txt.us,1430` with user `adotestuser` and password `Sq1234567`. Reached from `pywin32_testall`, not from import or install. The `25.223.161.222` address at line 57 sits in a `node == "xxx"` branch that does not run on a normal machine name.
- **Demo `urlopen` / `http.client` hits** (`isapi/samples/redirector*.py`, `win32/Demos/security/sspi/fetch_url.py`). Fixed demo URLs (`https://www.python.org`, `http://localhost/...`). `fetch_url.py` uses `base64` for an NTLM/SSPI Authorization header.
- **`info@enthough.com`.** Same typo in sdist `setup.cfg` and wheel `METADATA`. No code sends mail or fetches from that domain.
- **pywin32-ctypes `Libraries.__getattr__` (`ctypes/_util.py:72`, `cffi/_util.py:99`).** Loads a DLL named by the attribute. Every call site is `kernel32` or `advapi32`. Credential functions return data to the caller. They do not transmit it.
