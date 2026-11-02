# APB PWM to ideal RC demonstration

An APB-controlled PWM produces recorded digital samples. A feed-forward PWL bridge drives an ideal 10 kohm / 100 nF RC filter in ngspice. Five duty settings passed 80 periods each and 102,898 digital checks. Settled means met the 5 mV limit, and full responses agreed with an independent exact PWL/RC solution within 0.5 mV. Half-scale ripple measured 115.043 mV peak-to-peak. Bridge attenuation and flat-output negative controls were rejected.

The implementation and whitepaper were locally verified on 27 October 2026. **Crucible is beta.** These are bounded engineering demonstrations, with the exclusions below.

## Included files

`rtl/apb_pwm.v` owns the register interface and PWM. `tests/tb.v` records actual RTL samples. `scripts/bridge.py` converts them to PWL input. `verify.py` independently checks bridge levels/transitions and integrates the RC equation to compare all saved analogue samples.

The reviewed [PDF](docs/APB_PWM_RC_Mixed_Signal_Demo_Ignytion_A4.pdf) and [editable A4 PowerPoint](docs/APB_PWM_RC_Mixed_Signal_Demo_Ignytion_A4.pptx) are included. [Compact evidence](evidence/summary.json) records measured outcomes; [document hashes](evidence/documents.sha256.json) bind the final copies. Generated build artifacts and raw logs remain local and are excluded from Git.

## Prerequisites

Use Linux x86-64 or the tested Windows/WSL route, with an existing Crucible beta installation, Bash and Python 3. `crucible.lock` pins the managed tool versions and artifact identities. It does not install the external dependencies described here or establish support for native Windows/macOS/ARM hosts. Install the pinned host analysis dependencies from `requirements.txt` using your chosen Python environment.

Managed ngspice requires its native FFTW dependency (`libfftw3.so.3`) to be available. Supply that dependency through the system loader, `LD_LIBRARY_PATH`, or `NGSPICE_RUNTIME_DIR` in an ignored `local.env.sh` (see `config/example.env.sh`). This repository neither vendors the runtime nor copies one from another demo. The original workstation retains its already tested project-local runtime. No PDK is required for this ideal-source, ideal-RC experiment.

## 1. Choose the correct shell and directory

Run every Linux command below from this repository's root: the directory containing `crucible.toml`, `crucible.lock` and `scripts/`. The tested flow uses **WSL/Linux x86-64**. A Windows PowerShell block is labelled separately. Do not paste a PowerShell block into Bash or run a Bash block in PowerShell.

Crucible must already be installed in that Linux/WSL shell. A PDK, Tcl-capable Magic where required, and native runtime libraries are separate prerequisites; this repository does not provide an installation archive for them. Commands containing `/path/to/...` require your actual dependency location before execution.

## 2. Restore and inspect the Crucible environment

Linux/WSL Bash:

```bash
igny init
igny --version
igny workspace sync
igny status
igny env show ams-pwm-rc
igny tool show iverilog --env ams-pwm-rc
igny tool show ngspice --env ams-pwm-rc
```

`igny init` initializes the outer workbench shell. `workspace sync` reads the supplied lock, acquires missing pinned artifacts and restores the recorded environment. It may download large archives; it does not build this design, provision a PDK, or install every native library. `status` should identify this workspace, and `env show` should list the tools in `ams-pwm-rc`. `tool show` establishes the binary/provider resolution before a run.

Stop on an acquisition/binding error and inspect its reported log. A successful version or inventory command is a prerequisite check, not a design PASS. The commands below select the same project environment explicitly through the scripts.

## 3. Configure the native runtime and Python observer

No PDK is required. Managed ngspice needs a compatible FFTW library available to the native loader. When that library is already installed system-wide, no local configuration is needed. For a separate runtime directory, create/edit the ignored configuration:

```bash
if [ ! -f local.env.sh ]; then cp config/example.env.sh local.env.sh; fi
vi local.env.sh
source ./local.env.sh
mkdir -p build/runtime results
export LD_LIBRARY_PATH="$PWD/build/runtime${NGSPICE_RUNTIME_DIR:+:$NGSPICE_RUNTIME_DIR}:${LD_LIBRARY_PATH:-}"
igny run --env ams-pwm-rc ngspice --version
igny run --env ams-pwm-rc iverilog -V
```

Set `NGSPICE_RUNTIME_DIR` to the real directory containing `libfftw3.so.3`; remove unused placeholder exports. No runtime is copied from another demo or committed to this repository. This version probe must work before analogue simulation.

### Python observer setup

The measured route used the **Windows Python observer against WSL-generated files**. In Windows PowerShell, from this same repository root:

```powershell
python --version
python -m venv .venv-win
.\.venv-win\Scripts\python.exe -m pip install -r requirements.txt
.\.venv-win\Scripts\python.exe -c "import numpy; print('Observer imports available')"
```

Use that explicit virtual-environment interpreter for the PowerShell verification commands below; activation and execution-policy changes are unnecessary. The virtual environment is ignored by Git. Package installation needs access to the configured Python package index.

If running the observer entirely in Linux instead, install the same requirements in a Linux Python environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c "import numpy; print('Observer imports available')"
```

The two Python environments are alternatives. A Windows virtual environment cannot be used as a Linux interpreter. Independent clean-machine reproduction remains unverified.

## 4. Run the digital and analogue stages

Linux/WSL Bash:

```bash
bash scripts/run.sh digital
bash scripts/run.sh analogue
```

`digital` compiles/runs the APB/PWM testbench and records five 80-period CSV waveforms for duties 0, 64, 128, 192 and 256. `analogue` converts those actual samples into 0/1.8 V PWL sources, then runs all five ideal RC simulations. The bridge is recorded feed-forward; no live shared-library or feedback connection is claimed.

## 5. Run the independent observer and inspect its controls

Windows PowerShell:

```powershell
.\.venv-win\Scripts\python.exe scripts\verify.py
```

Or, with the Linux Python environment from step 3:

```bash
.venv/bin/python scripts/verify.py
```

Require `APB_PWM_BRIDGE_AND_RC_REFERENCE_VERIFIED`. The observer checks 102898 digital comparisons, every generated bridge level/transition, the full saved analogue waveforms against an independent exact PWL/RC solution within 0.5 mV, and settled means within 5 mV. It deliberately attenuates the bridge and corrupts the half-scale analogue response and requires rejection inside the same observer.

Inspect raw results in Bash:

```bash
cat results/digital.log
cat results/bridge.json
tail -n 20 results/analogue_128.log
cat results/summary.json
```

The expected means are 0, 0.45, 0.90, 1.35 and 1.80 V. The recorded half-scale ripple is approximately 115.043 mV peak-to-peak. The filter is an ideal 10 kohm resistor and 100 nF capacitor; these values do not establish physical component accuracy.

## 6. Troubleshooting

| Symptom | Check and next action |
|---|---|
| ngspice loader cannot find FFTW | Correct the native loader/runtime directory and repeat the step-3 version probe |
| Digital CSV missing | Run `digital` before `analogue` |
| PWL/bridge mismatch | Preserve actual CSV/PWL evidence and inspect `scripts/bridge.py`; do not replace recorded samples with an ideal duty source |
| Mean passes but pointwise comparison fails | Inspect the full response and time mapping; a mean alone is insufficient |
| NumPy import fails | Use the explicit observer interpreter prepared above |

## 7. Open the whitepaper and check the public Git candidate

Windows PowerShell, from the repository root:

```powershell
Invoke-Item .\docs\APB_PWM_RC_Mixed_Signal_Demo_Ignytion_A4.pdf
Invoke-Item .\docs\APB_PWM_RC_Mixed_Signal_Demo_Ignytion_A4.pptx
.\.venv-win\Scripts\python.exe scripts\preflight_git.py
```

The preflight script uses Python's standard library, so `python scripts/preflight_git.py` also works in an existing Python environment. It checks documentation links, the exact document hashes, indexed/unignored paths, shell index modes, selected credential/personal-path patterns and Git whitespace. This is a public-candidate check; it does not rerun EDA tools.

Linux/WSL Git review, after reviewing the files selected by the repository allowlist:

```bash
git status --short
git diff --check
git add -- .
git diff --cached --check
python3 scripts/preflight_git.py
git diff --cached --stat
git diff --cached
```

Do not force-add ignored build products, PDK/runtime payloads, raw logs, local configuration or agent/work notes. The repository contains no invented project-wide licence grant; upstream dependencies retain their own terms.

The following are **manual commit/publication commands**, not steps already performed by this project. Review the staged content and choose your own author identity and public destination first. Run `remote add` only when this repository has no `origin`:

```bash
git branch --show-current
git config user.name
git config user.email
git commit -m "Add verified AMS_PWM_RC demonstration and whitepaper"
PUBLIC_REPOSITORY_URL='REPLACE_WITH_YOUR_PUBLIC_REPOSITORY_URL'
git remote add origin "$PUBLIC_REPOSITORY_URL"
git push -u origin HEAD
```

Replace the destination placeholder before use. A new package is staged on `demo/verified`; the branch command confirms the actual current branch. If `origin` already exists, inspect it with `git remote get-url origin` and skip `remote add`. No commit, remote mutation or push is performed by the reproduction scripts.

## Limits

Recorded feed-forward simulation, with no live shared-library/XSPICE interface or analogue feedback. Ideal source and RC, static duties and sampled local time. No transistor driver model, tolerances, noise, PVT, physical hardware or signoff. The test covers its declared APB register contract rather than exhaustive APB compliance.
