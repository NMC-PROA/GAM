**Verdict: needs-attention.** I found no evidence of deliberate malware, credential exfiltration, or a concealed backdoor in the diff. The new updater nevertheless permits replacement of an audited fork with unaudited upstream binaries, and it inherits a configuration option that can disable TLS authentication.

These findings distinguish security weaknesses and trust changes from evidence of compromise.

**GAM-01 — Upstream releases become executable authority over the pinned fork**

- **Severity:** High for the stated pinned-fork requirement
- **Confidence:** High
- **Location:** [new/src/gam/__init__.py:4796](/Users/timmy/work/gam-review/audit/d752/new/src/gam/__init__.py:4796), execution at lines 4826 and 4845; replacement at 4837.
- **Quoted snippets:**

  ```python
  digest = asset.get('digest') or ''
  ...
  if hashlib.sha256(content).hexdigest() != digest[7:]:
  ```

  ```python
  result = subprocess.run([newGam, 'version', 'simple'],
                         capture_output=True, text=True,
                         timeout=300, env=env, check=False)
  ```

  ```python
  for entry in sorted(set(os.listdir(newPath)) | {'lib'}):
  ```

- **Why:** The SHA-256 check verifies consistency with the **same GitHub release API response that supplies the download URL**. It does not authenticate an independently approved fork build. There is no pinned commit, fork identity, approved digest, signature verification, or attestation verification.

  A compromised upstream publishing account or build pipeline could publish a matching archive and digest. The updater would execute it before replacing files. Printing the expected version is the execution check; malicious code can print that string. Neither Python verification run requires a zero exit status.

  The executable receives the caller’s privileges, almost the entire environment, inherited working directory, filesystem access, and ordinary network access. Subject to existing OS restrictions, it could read `oauth2.txt`, `oauth2service.json`, `client_secrets.json`, other accessible credentials, and environment secrets, then use Google APIs or exfiltrate them. This is a capability of the downloaded executable, **not observed exfiltration in this diff**.

  Replacement also has no release-file allowlist: credential/configuration files survive only when the archive does not contain their names. Rollback restores tracked file moves; it cannot undo credential theft or arbitrary actions already performed by the executable.

- **Confirm step:** Statically trace `doVersion` → `doGAMCheckForUpdates` → `doGAMUpdate`, and inspect all checks before lines 4826/4845. Confirm that the only archive approval is the API-supplied digest and that no fork-specific authorization gate exists.

**GAM-02 — Disabling ordinary API TLS validation also disables updater authentication**

- **Severity:** High, conditional on `no_verify_ssl = true` and an on-path attacker
- **Confidence:** High
- **Location:** [new/src/gam/__init__.py:4657](/Users/timmy/work/gam-review/audit/d752/new/src/gam/__init__.py:4657), asset request at 4789; shared HTTP configuration at 4459.
- **Quoted snippets:**

  ```python
  _, c = getHttpObj(timeout=10).request(GAM_LATEST_RELEASE, 'GET', ...)
  ```

  ```python
  resp, content = getHttpObj(timeout=300).request(
      asset['browser_download_url'], 'GET')
  ```

  ```python
  disable_ssl_certificate_validation=GC.Values[GC.NO_VERIFY_SSL],
  ```

- **Why:** The updater uses the ordinary configurable HTTP client without enforcing certificate validation. An on-path attacker could forge release metadata, supply a matching asset name and SHA-256 digest, and return a malicious archive. Digest comparison would pass because the attacker supplied both values.

  The asset URL receives no independent HTTPS, hostname, or repository-path validation. With forged metadata, it can also direct the download outside GitHub. The default is safe with respect to this setting: `NO_VERIFY_SSL: FALSE` in `glcfg.py:435`. The new issue is extending this existing insecure option to downloaded-code execution.

- **Confirm step:** Follow both updater requests into `getHttpObj`; verify that neither overrides nor rejects `NO_VERIFY_SSL`. Inspect `glcfg.py:223,435,613` for its meaning, default, and configurable status.

**GAM-03 — Checking another installation executes its unverified binary**

- **Severity:** Medium, conditional on selecting an attacker-controlled folder
- **Confidence:** High
- **Location:** [new/src/gam/__init__.py:4932](/Users/timmy/work/gam-review/audit/d752/new/src/gam/__init__.py:4932), helper at 4629–4644.
- **Quoted snippets:**

  ```python
  if targetPath is not None:
    currentVersion = _getGAMVersionAt(targetPath)
  ```

  ```python
  result = subprocess.run([gamExe, 'version', 'simple'],
                         capture_output=True, text=True,
                         timeout=300, env=env, check=False)
  ```

- **Why:** `version check path <folder>` and `version checkrc path <folder>` can execute `<folder>/gam` or `gam.exe`, despite being check commands. Update/install commands targeting an existing executable do this too, **before** contacting GitHub or verifying any download.

  The helper checks file existence and the reported version’s format, not executable provenance. A malicious local executable runs with the same credential access described in GAM-01. This requires an explicitly selected path; it is not a background execution path.

- **Confirm step:** Read the `if forceCheck` block in `doVersion`. Confirm that `_getGAMVersionAt` runs independently of `if update`, and that `os.path.isfile` is its only executable precondition.

**Updater behavior and cleared security checks**

| Area | Static result |
|---|---|
| Metadata origin | Existing constant resolves to `https://api.github.com/repos/GAM-team/GAM/releases/latest` (`__init__.py:193–203,4657`). |
| Archive origin | Taken directly from the selected asset’s `browser_download_url`. Intended origin is a GAM-team/GAM GitHub release download; the final host after redirects is not established by these sources. |
| Digest origin | Selected asset’s `digest` field in that same release response. No separate checksum file is downloaded. Missing/non-`sha256:` digest and mismatches fail before extraction or downloaded-code execution. |
| Asset selection | Matches OS and architecture. macOS/Linux select the newest compatible OS/glibc build; StaticX selects legacy compatibility. Filename version is not explicitly bound to the release’s version string. |
| TAR extraction | `tar.extractall(tempPath, filter='data')` at 4820 explicitly requests the standard-library containment/link/special-file safeguards. No unfiltered fallback. It does not additionally require every member to be under `gam7/`. No evident traversal bypass in the changed code. |
| ZIP extraction | Every member is checked before `extractall`: backslashes normalized for validation; leading `/`, leading drive letters, any `..` component, and names outside `gam7/` are rejected. **No evident Zip Slip bypass.** |
| Temporary directory | `mkdtemp(prefix='.gamupdate-', dir=gamPath)` keeps staging and renames on the installation filesystem. |
| Python subprocess environment | Copies `os.environ`, removes only `STATICX_PROG_PATH`, sets `PYINSTALLER_RESET_ENVIRONMENT=1`. No credential environment scrubbing, restricted identity, sandbox, network restriction, or explicit `cwd`. |
| Downloaded execution | Runs staged binary once, then installed binary once, both with `version simple` and a 300-second timeout. These are compatibility checks, not security checks. |
| Replacement | Moves existing entries matching staged top-level names, plus `lib`, into backup; moves staged entries into place. This is a sequence of renames, not one atomic installation swap. |
| Restore | Reverses installed moves, then backup moves, for caught failures. Retains recovery location when restore fails. Cannot reverse executed-code side effects. |
| Windows self-replacement | After staged verification, launches the helper asynchronously; waits for parent exit, swaps entries, runs installed binary, restores on failure, and retries move failures. Parent return does not establish final helper success. |
| Windows helper environment | `Popen` supplies no `env`, so it inherits the full environment; uses `close_fds=False`, permitting inheritable handles. It sets `PYINSTALLER_RESET_ENVIRONMENT` before installed verification. |
| Trigger | Replacement requires explicit `version update` or `version install` arguments, including commands supplied through existing batch mechanisms. Plain `version`, `simple`, `check`, `checkrc`, and help do not replace binaries. Path checks have GAM-03’s execution behavior. |
| Installation restrictions | Own-folder updates reject Homebrew and Python-source installations. Those installations can still install/update a different target folder. `install` requests the latest release even when it is not newer. |
| Disable setting | `no_update_check` is not consulted by these new paths. It does **not** prohibit explicit upstream installation or replacement. |
| OAuth on download requests | Both calls use raw `getHttpObj`, not `transportAuthorizedHttp`. No Google OAuth bearer token is explicitly attached by this updater code. |

**Windows `-EncodedCommand`: complete decoded template**

There is no fixed encoded blob in the repository. At runtime, lines 4741–4747 substitute the PID, installation path, temporary path, version, and quiet flag into the following plaintext, then encode it as **UTF-16LE → Base64**. Path/version substitutions double single quotes for PowerShell single-quoted strings. The encoding itself is not evidence of obfuscation.

The full decoded template from `__init__.py:4528–4626` follows. Runtime values are unavailable, so the original substitution markers are retained.

```powershell
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$gamPid = @@PID@@
$gamPath = '@@GAMPATH@@'
$tempPath = '@@TEMPPATH@@'
$version = '@@VERSION@@'
$quiet = @@QUIET@@
$newPath = Join-Path -Path $tempPath -ChildPath 'gam7'
$backupPath = Join-Path -Path $tempPath -ChildPath 'backup'
function Rename-Entry([string]$from, [string]$to) {
  if (Test-Path -LiteralPath $to) {
    throw "$to already exists"
  }
  $env:GAMUPDATE_FROM = $from
  $env:GAMUPDATE_TO = $to
  $ErrorActionPreference = 'Continue'
  $result = (& cmd.exe /d /c move /y '"%GAMUPDATE_FROM%"' '"%GAMUPDATE_TO%"' 2>&1 | Out-String).Trim()
  $rc = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
  if ($rc -ne 0) {
    throw "Could not move $from to ${to}: $result"
  }
}
# Wait, at most 5 minutes, for the GAM that started the update to exit
for ($wait = 0; ($wait -lt 1200) -and (Get-Process -Id $gamPid -ErrorAction SilentlyContinue); $wait++) {
  Start-Sleep -Milliseconds 250
}
# Like the installer, replace lib even if the new version does not have one; files not in the release, e.g., oauth2.txt, are not touched
$entries = @(@(Get-ChildItem -LiteralPath $newPath -Force | ForEach-Object { $_.Name }) + @('lib') | Sort-Object -Unique)
$installed = @()
$backedUp = @()
function Restore-Previous {
  for ($i = $script:installed.Count - 1; $i -ge 0; $i--) {
    Rename-Entry (Join-Path -Path $gamPath -ChildPath $script:installed[$i]) (Join-Path -Path $newPath -ChildPath $script:installed[$i])
  }
  for ($i = $script:backedUp.Count - 1; $i -ge 0; $i--) {
    Rename-Entry (Join-Path -Path $backupPath -ChildPath $script:backedUp[$i]) (Join-Path -Path $gamPath -ChildPath $script:backedUp[$i])
  }
  $script:installed = @()
  $script:backedUp = @()
}
$failure = ''
# Another GAM may still be running from this folder (its lib can not be renamed); try for about a minute
for ($try = 1; $try -le 20; $try++) {
  $failure = ''
  try {
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    foreach ($entry in $entries) {
      $current = Join-Path -Path $gamPath -ChildPath $entry
      $new = Join-Path -Path $newPath -ChildPath $entry
      if (Test-Path -LiteralPath $current) {
        Rename-Entry $current (Join-Path -Path $backupPath -ChildPath $entry)
        $backedUp += $entry
      }
      if (Test-Path -LiteralPath $new) {
        Rename-Entry $new $current
        $installed += $entry
      }
    }
# Run the installed version once; anything but the expected version puts the previous one back
    $env:PYINSTALLER_RESET_ENVIRONMENT = '1'
    $ErrorActionPreference = 'Continue'
    $result = (& (Join-Path -Path $gamPath -ChildPath 'gam.exe') version simple 2>&1 | Out-String).Trim()
    $rc = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($result -ne $version) {
      $failure = "Downloaded GAM did not run correctly on this system, expected version: $version, rc: $rc, output: $result"
    }
  } catch {
    $ErrorActionPreference = 'Stop'
    $failure = $_.Exception.Message
  }
  if (-not $failure) {
    break
  }
  try {
    Restore-Previous
  } catch {
    Write-Output ('GAM update could not restore the previous version; its files are in {0}, move them back to {1}' -f $backupPath, $gamPath)
    exit 1
  }
  if ($failure -like 'Downloaded GAM did not run*') {
    break
  }
  Start-Sleep -Seconds 3
}
if ($failure) {
  Remove-Item -LiteralPath $tempPath -Recurse -Force -ErrorAction SilentlyContinue
  Write-Output "GAM update failed, GAM not updated: $failure"
  if ($failure -notlike 'Downloaded GAM did not run*') {
    Write-Output 'If another GAM was running from this folder, wait for it to finish and run gam version update again'
  }
  exit 1
}
Remove-Item -LiteralPath $tempPath -Recurse -Force -ErrorAction SilentlyContinue
if (-not $quiet) {
  Write-Output "GAM updated to version ${version}: $gamPath"
}
exit 0
```

The helper invokes PowerShell, `cmd.exe` for moves, and the installed `gam.exe`. It contains no downloader, credential-reading command, persistence mechanism, or additional network destination. Its single-quote escaping and environment-variable move operands show deliberate handling of path quoting; I found no evident injection in the intended substitutions.

**Exact coverage and classification of every changed hunk**

Reviewed **all 1,433 lines, 70 hunks, seven changed files** in `changes.diff`, against the supplied old/new files and relevant surrounding code. Below, numbers are **new-side hunk starting lines**, allowing every hunk to be accounted for.

For the `src/gam/__init__.py` rows, the filename is abbreviated to `__init__.py`.

| File / hunk starts | Count | Classification |
|---|---:|---|
| `.github/workflows/build.yml`: 84 | 1 | Feature: adds `xcode-27` build matrix entry; runner trust requires confirmation below. |
| `pyproject.toml`: 9 | 1 | Dependency maintenance: two existing exact pins bumped; artifacts unverified. |
| `src/GamCommands.txt`: 1391, 1838, 1858, 6489, 7134, 7181, 8276, 8290, 9068, 9076 | 10 | Benign documentation: updater, attendee mapping, move filters, command grouping and whitespace. |
| `src/GamUpdate.txt`: 1 | 1 | Benign release notes through unreleased 7.52.04; not relied upon as proof of implementation safety. |
| `__init__.py`: 25, 66, 76, 181 | 4 | Version bump, standard-library imports, Homebrew detection supporting updater restrictions. |
| `__init__.py`: 4517, 4663 | 2 | Updater feature; GAM-01–03 apply. Includes relocated/expanded `doVersion`. |
| `__init__.py`: 9326, 9508, 9547 | 3 | Bugfixes: Sheets wrapping/number formatting and CSV upload selection; handle ACL conflict errors. |
| `__init__.py`: 10210 | 1 | Benign removal of old `doVersion` after relocation; no second hidden implementation. |
| `__init__.py`: 14030, 14046, 14262, 14312, 14955, 14979, 15011, 15069, 15084, 15103, 15185, 15200 | 12 | Bugfixes: handle Reports API `permissionDenied` alongside existing errors; no authorization bypass or new destination. |
| `__init__.py`: 42692, 43040, 43168, 43220, 43258, 43267, 56471 | 7 | Feature/documentation: explicitly requested calendar attendee-domain mapping. Target domain comes from command arguments; no fixed external recipient. |
| `__init__.py`: 58326 | 1 | Feature support: reports whether MIME filters are defined. |
| `__init__.py`: 64221, 64244, 64317, 64337, 64388 | 5 | Feature/refactor: shared copy/move filters, move-subfile ownership options and defaults. |
| `__init__.py`: 64438 | 1 | Benign equivalent refactor to `max(n, tcnt)`. |
| `__init__.py`: 64634, 65790 | 2 | Bugfix: handle Google Drive ACL conflicts. |
| `__init__.py`: 64945, 65855 | 2 | Benign copy/move command documentation. |
| `__init__.py`: 65170, 65180 | 2 | Copy-filter behavior adjustment when ownership metadata is absent; ordinary feature/bugfix scope, no concealed recipient or egress. |
| `__init__.py`: 66138, 66197, 66219, 66230, 66279, 66307 | 6 | Feature: enforce requested move filters, retrieve/remove ownership fields appropriately, retain source folders for selective moves, correct reported target name. |
| `__init__.py`: 69179, 69207, 69328, 69443, 69603 | 5 | Bugfixes: propagate existing `useDomainAdminAccess` to name lookups; handle ACL conflicts. No new unconditional admin-access setting. |
| `__init__.py`: 76896 | 1 | Bugfix: correct exception class capitalization for attachment upload failures. |
| `src/gam/gamlib/glgapi.py`: 219 | 1 | Bugfix support: add `CONFLICT` to ACL error reasons. |
| `src/gam/gamlib/glmsgs.py`: 249, 286 | 2 | Benign updater messages and whitespace adjustment. |

The directory comparison identified the same seven differing files. `src/LICENSE` and `src/README.md` are identical dangling symlinks in these supplied snapshots; their missing target contents were unavailable. The supplied source reports **7.52.04**, consistent with the described unreleased fix. Commit identities are taken from your labels, not independently authenticated.

Additional context inspected included command dispatch/startup, HTTP construction and authorization wrappers, configuration defaults and credential paths, build/install/signing/attestation steps, dependency-update workflow, and package exclusions. No repository code was executed, imported, installed, or built; no network was used.

**Build and dependency observations**

- **`xcode-27` — unusual runner label, unverified provenance.** [build.yml:87](/Users/timmy/work/gam-review/audit/d752/new/.github/workflows/build.yml:87) adds only a matrix entry. It changes no triggers, action references, permissions, scripts, or secret names. However, `runs-on: ${{ matrix.os }}` sends the existing build—including Google authentication and macOS signing/notarization steps—to whichever runner resolves that label. The repository cannot establish whether it is an approved hosted image or an organization runner. **Confirm:** inspect the organization’s runner inventory and retained job metadata for its provider, ownership, isolation, and image. Do not infer trust from the label alone.
- **`chardet 7.6.0 → 7.7.0`; `filelock 4.2.0 → 4.2.6`.** [pyproject.toml:12](/Users/timmy/work/gam-review/audit/d752/new/pyproject.toml:12) retains existing package names and exact-version syntax. No new index, direct URL, VCS source, build backend, or installation hook appears. The version numbers alone provide no evidence of compromise. **Their package contents are not cleared:** no corresponding distributions, hashes, or provenance evidence were supplied. Confirm using separately obtained, approved artifacts and source comparisons.
- Existing CI already installs dependencies without artifact hashes, uses some moving tool/action references, and runs downloaded bootstrap scripts. Those are **baseline practices, not introduced by this diff**. The new runner inherits them. Existing build attestations are not verified by the new updater.

**URLs, domains and IPs**

No new hard-coded unexpected domain or IP was found in the added lines. The added literal release URL is the expected `https://github.com/GAM-team/GAM/releases`.

The significant new egress capability is **metadata-selected archive downloading**, including HTTP-library redirects, without a local destination allowlist. The fixed GitHub API URL already existed. Existing non-Google/GAM infrastructure in build context—such as Rust/Python bootstrap and signing services—was unchanged.

**Cleared**

- No observed new credential/token collection or exfiltration routine.
- No implicit/background self-replacement call site.
- No evident ZIP traversal bypass or unfiltered TAR extraction.
- No hidden executable payload in the PowerShell encoding.
- No new hard-coded attacker endpoint, dependency-name substitution, or CI secret-disclosure command.
- All other changed code hunks are explainable as the features, fixes, or refactors classified above.

“Cleared” applies to the reviewed source changes, not future upstream binaries, dependency distributions, or runner infrastructure.

**Required changes for a pinned fork**

1. **Remove or hard-reject both `version update` and `version install` before path probing or network access.** Also disable `doGAMUpdate` itself so alternate callers cannot bypass command parsing. This is the simplest reliable way to prevent upstream replacement.
2. Remove `_getGAMVersionAt` execution from check commands; reject `path` there or read a trusted, non-executable version manifest.
3. Keep updates in a separate reviewed deployment process using immutable fork artifacts and independently approved hashes/provenance. Changing `GIT_USER` or setting `no_update_check` alone is insufficient.
4. If an installer remains, require verified TLS, constrained HTTPS destinations/redirects, approved archive contents excluding credentials/configuration, and fork-authorized artifacts **before any execution**. Run compatibility checks without production credentials and require successful exit status.