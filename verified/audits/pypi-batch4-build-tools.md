💡agent-bootstrap 0.2.9 loaded.

I'll review the pinned build-tool artifacts statically: provenance first, then install hooks, pattern hits, and the two high-risk packages (PyInstaller bootloader and patchelf-wrapper).The assignment is the ten build packages. I'll read provenance and each package's triage before opening install hooks and the two high-risk trees.Triage shows no sdist/wheel Python diffs. Next I’ll read install hooks, binary inventories, and the high-signal call sites.| package | version | provenance | verdict | reason |
|---|---|---|---|---|
| pyinstaller | 6.22.3 | attested 0/4 | PASS | Bundler/loader calls match upstream PyInstaller. No install-time download. Bootloader bytes were not in the extract. |
| pyinstaller-hooks-contrib | 2026.9 | attested 0/2 | PASS | Entry point only returns hook directories. Exec sites are OpenCV and pyqtgraph hook logic. |
| setuptools | 84.2.1 | attested 0/2 | PASS | `.pth`, pip fetch, and PyPI classifier download match upstream setuptools. |
| altgraph | 0.17.5 | attested 0/2 | PASS | Ronald Oussoren metadata. `os.system` only launches Graphviz. |
| macholib | 1.16.4 | attested 0/2 | PASS | Same maintainer and setup template. `ctypes` is a dyld lookup. |
| pefile | 2024.8.26 | attested 0/2 | PASS | Ero Carrera metadata. `urlopen` loads a caller-supplied signature file. |
| pyelftools | 0.33 | attested 0/2 | PASS | Eli Bendersky metadata. `zlib` inflates compressed ELF sections. |
| colorama | 0.4.6 | attested 0/2 | PASS | Jonathan Hartley / tartley. `ctypes` is kernel32 console calls. |
| pywin32-ctypes | 0.2.3 | attested 0/2 | REVIEW | Author email domain is `enthough.com`. No code contacts that domain. |
| patchelf-wrapper | 1.2.0 | absent from provenance triage | PASS | Install compiles the embedded tarball only. No fetch. Snapshot id `0.11.20200609.d6b2a72`. |

No package is FAIL. Every package above has `wheel_py_differs_from_sdist: []` and `wheel_py_not_in_sdist: []`. Trust for the attested-0 packages is the PyPI maintainer account alone.

## pyinstaller 6.22.3

Metadata points at `https://github.com/pyinstaller/pyinstaller` and `https://pyinstaller.org`, authors Hartmut Goebel, Giovanni Bajo, David Vierra, David Cortesi, Martin Zibricky. Dependencies are the expected set (`setuptools`, `altgraph`, `macholib`, `pefile`, `pywin32-ctypes`, `pyinstaller-hooks-contrib>=2026.7`, `packaging`). Entry points are the six `pyi-*` / `pyinstaller` console scripts.

`hatch_build.py` injects `PyInstaller/bootloader/<platform>/*` into the wheel and, only if that bootloader file is missing, runs `python ./waf configure all` in the local `bootloader/` tree. It does not download.

```58:68:review/build/pyinstaller/SDIST_pyinstaller-6.22.3/pyinstaller-6.22.3/hatch_build.py
    def compile_bootloader(self):
        import subprocess
        from PyInstaller import HOMEPATH

        src_dir = os.path.join(HOMEPATH, 'bootloader')
        additional_args = os.getenv('PYINSTALLER_BOOTLOADER_WAF_ARGS', '').strip().split()
        cmd = [sys.executable, './waf', 'configure', 'all']
        cmd += additional_args
        rc = subprocess.call(cmd, cwd=src_dir)
```

The sdist extract also has `bootloader/update-waf.sh`, a maintainer script. It downloads pinned `https://waf.io/waf-2.0.20.tar.bz2`, checks the `.asc` signature, and if key `49B4C67C05277AAA` is absent fetches `https://gitlab.com/ita1024/waf/raw/master/utils/pubkey.asc` (unpinned `master`). `hatch_build.py` does not call this script. `bootloader/build.sh` drives Vagrant guests and does not fetch a URL.

Code paths that look like loaders are the bundler itself:

- `building/build_main.py:1213` `exec(code, spec_namespace)` runs the user's `.spec`.
- `loader/pyimod02_importers.py:457` `exec(bytecode, module.__dict__)` is the frozen importer.
- `loader/pyimod01_archive.py:136` and `archive/writers.py:244` `marshal.loads` is the PYZ archive format.
- `isolated/_child.py:48-50` base64-then-marshal over a pipe from the parent `Popen`. The child runs a function the parent just serialized. `archive/pyz_crypto.py` raises `RemovedCipherFeatureError`.
- `hooks/rthooks/pyi_rth_multiprocessing.py:64` `exec(command)` only after `command.startswith` one of three `multiprocessing` helper prefixes.
- `lib/modulegraph/modulegraph.py:2952` is `urllib.request.pathname2url`, a path-to-file-URL helper.

macOS wheel `RECORD` lists four bootloaders that are not in the extracted tree: `Darwin-64bit/run` (171136), `run_d` (187704), `runw` (190488), `runw_d` (223416), plus two `.icns` icons. Triage classified binaries only for the Windows wheels: `run.exe`, `runw.exe`, `run_d.exe`, `runw_d.exe` on Windows-32bit-intel, Windows-64bit-intel, and Windows-64bit-arm (sizes 263680–349184). Those bytes were not extracted either. Linux wheels are in the triage file with `bins=0` because the scanner keyed off `.exe`.

## patchelf-wrapper 1.2.0

Not listed in `triage/provenance.txt` or `triage/prov-build.json`. `PKG-INFO` says Jim Porter, `itsjimporter@gmail.com`, `https://github.com/jimporter/patchelf-wrapper`, BSD. `__init__.py` is `version = '1.2.0'`.

`setup.py` (226 lines, read whole) never opens a URL. `BuildPatchelfCommand` extracts `patchelf_wrapper/patchelf-0.11.tar.gz` and runs `./configure` and `make`. `InstallLibCommand.run` always runs `install_patchelf` first. `check_patchelf` is `which patchelf` and skips the build when one is already on `PATH`. `CleanPatchelfCommand.initialize_options` sets `self.download_dir = None` and never reads it. Optional `pypandoc.convert` only rewrites the local README.

Embedded tarball: 192369 bytes, SHA256 `9602ff1cf5ece01f41bf427d152126c8af85b90dddbe15a494e3e69f73cfbccc`, 59 members, all under `patchelf-0.11/`. No absolute paths, `..`, links, or special nodes. Layout is an autotools dist: `configure`, `configure.ac`, `src/patchelf.cc`, `src/elf.h`, `build-aux/*`, tests, `COPYING`. `version` is `0.11.20200609.d6b2a72`, so this is a 2020-06-09 snapshot on the 0.11 line, while the README says "patchelf 0.11". `configure.ac` (785 bytes) adds `--with-page-size` (`getconf PAGESIZE`, default 4096) and `AC_DEFINE_UNQUOTED(PAGESIZE, ...)`. `patchelf.cc` (1778 lines) uses it once: `static int pageSize = PAGESIZE`. Counts in that file: `system(` 0, `popen(` 0, `execv` 0, `socket` 0, `dlopen` 0. The only URL in `patchelf.cc` is `http://www.gnu.org/licenses/`. Fourteen `tests/no-rpath-prebuild/no-rpath-*` files are ELF (`7f454c46`), 7197–10745 bytes, with no URL strings. I did not byte-compare this tarball to the NixOS `0.11` tag (no local upstream tree).

## setuptools 84.2.1

Author Python Packaging Authority, `distutils-sig@python.org`, source `https://github.com/pypa/setuptools`. Runtime dependencies are empty; packaging libraries are vendored.

`distutils-precedence.pth` is the known startup shim, generated by sdist `setup.py` class `install_with_pth`:

```1:1:review/build/setuptools/WHEEL_setuptools-84.2.1-py3-none-any/distutils-precedence.pth
import os; var = 'SETUPTOOLS_USE_DISTUTILS'; enabled = os.environ.get(var, 'local') == 'local'; enabled and __import__('_distutils_hack').add_shim();
```

`_distutils_hack/__init__.py` replaces stdlib `distutils` with `setuptools._distutils`. The report URL is `https://github.com/pypa/setuptools/issues/new?template=distutils-deprecation.yml`.

Triage flag `files_not_in_RECORD` is wrong for the files it names. `RECORD` lines 1–10 hash `distutils-precedence.pth`, `_distutils_hack/__init__.py`, `_distutils_hack/override.py`, and `setuptools/__init__.py` through `setuptools/_itertools.py`.

Network: `setuptools/installer.py:100-121` runs `python -m pip wheel` for a missing build egg (deprecated installer, index from `PIP_INDEX_URL` or `easy_install` config). `config/_validate_pyproject/formats.py:151-158` downloads `https://pypi.org/pypi?:action=list_classifiers` with `ssl.create_default_context()` when `trove-classifiers` is absent and `NO_NETWORK` is unset. Vendored `jaraco/context/__init__.py` `tarball()` can `urlopen` an arbitrary URL; nothing else in this tree calls it.

Eight launchers are inventoried (`cli-32.exe` / `cli.exe` share hash prefix `32acc1bc543116cb`, size 11776; `gui-32.exe` / `gui.exe` share `85dae1e95d77845f`). They were not in the extracted tree.

## pywin32-ctypes 0.2.3 — REVIEW

Homepage and sdist URL are `https://github.com/enthought/pywin32-ctypes`. Author is Enthought Inc. The email domain drops a `t`:

```4:6:review/build/pywin32-ctypes/SDIST_pywin32-ctypes-0.2.3/pywin32-ctypes-0.2.3/setup.cfg
url = https://github.com/enthought/pywin32-ctypes
author = Enthought Inc.
author_email = info@enthough.com
```

Wheel `METADATA` line 7 repeats `Author-email: info@enthough.com`. Sdist and wheel agree, so this is not a wheel-only injection. A scan of the 34 Python files found no `http`, `urlopen`, `exec`, `eval`, or `os.system`. `win32ctypes/pywin32/win32cred.py` and `core/ctypes/_authentication.py` are ctypes wrappers of Win32 `CREDENTIAL` / `CredWrite` / `CredRead`. Copyright headers say Enthought, Inc., Austin, TX. Confidence this email is a malicious contact channel: low. It is still an ownership mismatch a human should check against upstream, because the package has no attestation.

## Coverage and limits

Read whole: patchelf-wrapper `setup.py`, `setup.cfg`, `PKG-INFO`, `README.md`, `__init__.py`; the embedded tarball's member list, `version`, `configure.ac`, both `Makefile.am`, `README.md`, and the head, tail, and `PAGESIZE` sites of `patchelf.cc`. Also setuptools `setup.py`, `pyproject.toml`, the `.pth`, `installer.py`, the classifier downloader, `launch.py`, and `build_meta.run_setup`. Also PyInstaller `pyproject.toml`, `hatch_build.py`, `update-waf.sh`, `build.sh`, `isolated/_child.py`, `configure.py` through the UPX probe, `pyz_crypto.py`, and the exec/marshal sites cited above. Also hooks-contrib `setup.py`, `__init__.py`, `hook-cv2.py` (the config exec), `pyi_rth_pyqtgraph_multiprocess.py`, `hook-pylsl.py`, `hook-pyodbc.py`. Also pefile `setup.py` and `peutils.__load`, altgraph `Dot.py` command builders and `eval_marker`, macholib `dyld.py` header and the same `eval_marker`, colorama `pyproject.toml` and `initialise.py`, pywin32-ctypes `setup.py` / `setup.cfg` / `win32cred.py` / `_authentication.py` header, pyelftools `pyproject.toml`, `readelf.py` header, and the zlib block in `sections.py`.

Scanned, not read line by line: all 10 trees for `exec` / `eval` / `urlopen` / `subprocess` / `os.system` / `b64decode` / `marshal.loads` / `pickle.loads` / `verify=False` and for URL hosts (1302 URL hits; hosts were GitHub, Read the Docs, PyPA, Microsoft docs, and similar). Hooks-contrib is 714 Python files; setuptools is 229 plus vendored copies. PyInstaller pattern-hit files beyond the sites above were sampled through that scan.

Not inspected as bytes: PyInstaller Windows `run*.exe` (hash prefixes and sizes only), the four Darwin bootloaders named in the macOS `RECORD`, Linux/musl bootloaders, setuptools `cli*.exe` / `gui*.exe`, and the PyInstaller C bootloader sources (the sdist extract kept build scripts only). No artifact was executed, imported, or built.

## Cleared

- `update-waf.sh` downloads waf 2.0.20 and verifies a signature. The pubkey URL is unpinned `master`. The script is not on the install path.
- `0xc0decafe.com` is a comment in `PyInstaller/utils/win32/winutils.py:62` about PE timestamps.
- `download.nvidia.com` is a comment in `PyInstaller/depend/dylib.py:209`.
- `utils/hooks/__init__.py:128` `eval(txt)` evals stdout of a hook statement run in a spawned interpreter. `utils/misc.py:122` `eval(f.read())` loads a pprint'd data file.
- hooks-contrib `get_hook_dirs` returns `stdhooks/` and the package dir, then may raise the recursion limit to 1900 or 5000. `__import__` hits in the sklearn array-api hooks are comments.
- setuptools `wheel.py:229` `def eval` calls `req.marker.evaluate`. `_distutils/compilers/C/base.py:1130` evals the literal `'"static", "shared", "dylib", "xcode_stub"'`. `_vendor/packaging/_structures.py:10` mentions `pickle.loads` in a comment. `jaraco/functools` `eval(use)` is the vendored `except_(..., use='args[0]')` helper.
- altgraph and macholib `setup.py:68` `eval_marker` evaluates markers from their own `setup.cfg`.
- pefile `peutils.py:400` `urlopen(filename)` runs only when the signature path is not a local file.
- pyelftools `sections.py:102` `zlib.decompressobj()` inflates `ELFCOMPRESS_ZLIB` section bytes. `readelf.py` is the public-domain CLI, shipped as a data script.
- colorama `win32.py:41-101` binds `windll.kernel32` console APIs. `initialise.py` `atexit` calls `reset_all` to restore the console.
- patchelf `tar.extractall` has no filter. Member names have no traversal. The 14 prebuilt test ELFs match upstream's `no-rpath-prebuild` fixtures.
