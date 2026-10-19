# InteractiveELEC5622

Interactive, zoomable tree of the ELEC5622 course content. Click a node to read its
definition; use `+` to add new child nodes. See [WORKFLOW.md](WORKFLOW.md) for the plan.

## Setup (Windows, PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --use-feature=truststore --upgrade pip
python -m pip install -r requirements.txt
```

`--use-feature=truststore` makes pip use the Windows certificate store. It was needed on
this machine because plain pip failed with `CERTIFICATE_VERIFY_FAILED` (a network or
antivirus proxy re-signs HTTPS traffic).

## Run (once the app exists)

```powershell
python -m app.main
```
Then open http://127.0.0.1:8050.

## Test

```powershell
python -m pytest
```
