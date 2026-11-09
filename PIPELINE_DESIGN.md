# Project 5 — DevSecOps Pipeline Design Document

Deliverable 4.

## ✅ Executed results (2026-11-09, local run on Windows)
All four gates were run against both states; full log:
[`GATE_EVIDENCE.txt`](GATE_EVIDENCE.txt). Tools: bandit 1.9.4, pip-audit 2.10.1
(Gate 2 locally — Safety now requires an API key, so it stays the CI gate),
gitleaks 8.30.1, custom `inject_scanner.py`.

| Gate | Fail state | Fix state |
|------|-----------|-----------|
| 1 Bandit | **EXIT 1** — `eval` B307 at `app.py:12` (Medium) | EXIT 0 — No issues identified |
| 2 pip-audit | **EXIT 1** — 63 CVEs in 6 packages | EXIT 0 — No known vulnerabilities |
| 3 gitleaks | **EXIT 1** — 3 leaks in `config.py` | EXIT 0 — no leaks found |
| 4 inject_scanner | **EXIT 1** — hardcoded `SYSTEM_PROMPT` + injection phrase | EXIT 0 — clean |

EXIT≠0 means the gate **fails the pipeline** (blocks the commit).

## Repo layout
- `.github/workflows/security.yml` — the 4 sequential gates (runs on every push).
- `inject_scanner.py` — custom Gate 4 (pure Python, cross-platform).
- `config.py`, `app.py`, `requirements.txt` — **fail state** (the deliberate
  4-problem commit) at repo root.
- `fix_state/` — corrected copies to swap in for the fix commit.

## What each gate checks, and what it caught in the fail commit
| Gate | Tool | Checks | Caught in fail commit |
|------|------|--------|-----------------------|
| 1 | Bandit SAST | Insecure Python patterns; fails on **Medium+** severity (Bandit rates `eval` as Medium) | `eval()` in `app.py` (B307) |
| 2 | Safety (CI) / pip-audit (local) | CVEs in `requirements.txt`; fails on Critical/High | `flask==0.12.2`, `requests==2.19.1`, `pyyaml==5.1`, `jinja2==2.10` → 63 CVEs |
| 3 | Gitleaks | Secrets in the commit diff, using custom `.gitleaks.toml` org rules | `API_KEY`/`DB_PASSWORD` in `config.py` (3 leaks) |
| 4 | inject_scanner.py | Hardcoded `SYSTEM_PROMPT`/`system_message`/`"role":"system"` + injection phrases | `SYSTEM_PROMPT = …` and "ignore previous instructions" in `app.py` |

**Tooling notes**
- **Gate 1 threshold:** Bandit classifies `eval` as *Medium* severity, so the
  workflow uses `--severity-level medium --confidence-level medium`; a High-only
  threshold would let the fail commit pass.
- **Gate 2:** the Safety CLI now requires a (free) API key / login, so the gate
  was executed **locally with `pip-audit`** (same CVE database behaviour);
  Safety remains in `security.yml` for CI, where `SAFETY_API_KEY` is supplied as
  a secret. `pip-audit -r requirements.txt` is the drop-in local equivalent.
- **Gate 3:** `.gitleaks.toml` extends the default ruleset with TechCorp
  patterns so the planted secrets are detected; the fix state (env lookups) is
  allow-listed and passes.

## The 4 deliberate problems and their fixes
| # | Problem (fail state) | Fix (fix_state) |
|---|----------------------|-----------------|
| 1 | Hardcoded API key in `config.py` | `os.environ.get("API_KEY")` |
| 2 | Vulnerable pinned deps in `requirements.txt` | Upgraded to current safe pins |
| 3 | `eval()` in `app.py` | Safe `ast`-based arithmetic evaluator |
| 4 | Hardcoded `SYSTEM_PROMPT` in `app.py` | Moved to `os.environ.get("SYSTEM_PROMPT")` |

## Run the gates (fail commit → fix commit)

**1. Push the fail commit** (files already at root) → all 4 gates fail.

**2. Apply the fix and push again:**
- **Linux / Kali:** `cp fix_state/*.py . && cp fix_state/requirements.txt . && git commit -am "fix: remediate all 4 gates" && git push`
- **Windows (PowerShell):** `Copy-Item fix_state\*.py . -Force ; Copy-Item fix_state\requirements.txt . -Force ; git commit -am "fix: remediate all 4 gates" ; git push`
→ all 4 gates pass.

## Run the gates locally before pushing (the exact commands executed here)
Install once: `pip install bandit pip-audit` and gitleaks
(`winget install Gitleaks.Gitleaks` on Windows, `brew install gitleaks` on
Linux/mac). Same commands on Linux/Kali and Windows (PowerShell):
```bash
# Gate 1 - Bandit (Medium+ threshold, because eval is rated Medium)
bandit -r . --severity-level medium --confidence-level medium

# Gate 2 - dependency CVEs (pip-audit local equivalent of the Safety CI gate)
pip-audit -r requirements.txt

# Gate 3 - secrets (custom org rules in .gitleaks.toml)
gitleaks detect --no-git --source . -c .gitleaks.toml -v

# Gate 4 - custom injection scanner
python inject_scanner.py .
```
Each exits non-zero on the fail state and 0 on the fix state — see
`GATE_EVIDENCE.txt`.

## Why catch these at commit time
Blocking secrets, vulnerable dependencies, dangerous code constructs, and
hardcoded prompts at commit time means they never reach a build artifact or
production. A leaked key in `git` history is already compromised; a vulnerable
dependency in a release is exploitable by anyone; `eval()` shipped to prod is
RCE. Shifting these checks left turns a costly production incident into a
30-second failed pipeline the author fixes before merge.
