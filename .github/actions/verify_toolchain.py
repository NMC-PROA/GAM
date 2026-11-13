#!/usr/bin/env python3
"""Fail the build unless every Python+OpenSSL toolchain archive that
jay0lee/python-openssl-latest downloaded matches the pinned SHA-256 table
(.github/locks/toolchain-sha256.txt, from release v1.2026.11.08.1052).

The upstream installer (scripts/install.py) does not check any digest and
falls back to unverified TLS when certifi is missing, so this runs right
after it and before any signing or upload step. Fails closed if no archive
is found.
"""
import hashlib, os, pathlib, sys

table = {}
for line in pathlib.Path(__file__).resolve().parents[1].joinpath("locks/toolchain-sha256.txt").read_text().splitlines():
    if line.strip():
        digest, name = line.split(None, 1)
        table[name.strip()] = digest.lower()

tmp = pathlib.Path(os.environ.get("RUNNER_TEMP", "/tmp"))
found = [p for p in tmp.iterdir() if p.name.startswith("python-") and "-openssl-" in p.name and p.name.endswith((".tar.xz", ".zip"))]
if not found:
    sys.exit(f"verify_toolchain: no python-*-openssl-* archive found in {tmp}; refusing to continue")
bad = False
for p in sorted(found):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    want = table.get(p.name)
    ok = want == h.hexdigest()
    print(f"{'OK  ' if ok else 'FAIL'} {p.name} {h.hexdigest()}" + ("" if ok else f" (pinned: {want})"))
    bad |= not ok
sys.exit(1 if bad else 0)
