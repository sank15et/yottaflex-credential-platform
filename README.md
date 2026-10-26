# YottaFlex Credential Platform

A Python/SQLite project for generating and validating a credential-issuance dataset, with service logic for issuing, verifying, and revoking credentials.

> **Project status:** The generated baseline dataset, SQL import, foreign-key checks, lifecycle checks, and current service tests have been run locally. The anomaly fixture validator checks the four required fixture scenarios, but it does not by itself prove that every fixture has been exercised end-to-end through the API.

## Features

- SQLite schema for learners, courses, enrollments, issuers, credential rules, completion records, credentials, verification requests, revocations, and audit events.
- Deterministic synthetic-data generation with a fixed seed.
- CSV and JSON exports plus a SQL seed file.
- Separate anomaly fixtures and ground-truth labels.
- Credential payload hashing using SHA-256 to detect payload changes.
- Service logic for credential issuance, verification, and revocation.
- Unit tests for issuance, duplicate prevention, invalid completion timing, revocation behavior, missing credentials, and tamper detection.
- A validation script for the four required anomaly fixtures.

## Technology

- Python
- SQLite
- FastAPI and Uvicorn (API dependencies)
- Python `unittest`

## Repository layout

```text
.
├── data/
│   ├── generated-final/        # Generated full-scale exports (created locally)
│   └── credentials.db          # Application database (if initialized locally)
├── docs/
│   └── ASSUMPTIONS_AND_LIMITATIONS.md
├── prompts/
│   └── AI_PROMPT_HISTORY.md
├── scripts/
│   └── validate_anomalies.py
├── src/
│   ├── database.py
│   ├── generator.py
│   ├── main.py
│   └── services.py
├── tests/
│   └── test_services.py
├── schema.sql
├── requirements.txt
└── README.md
```

Actual generated output and local database files may be excluded from Git depending on `.gitignore`. If reviewers need the full generated dataset, follow the submission brief and repository-size limits when deciding whether to commit it or provide a reproducible generation command.

## Setup

Use Python 3.11+ where possible; the project has also been exercised with Python 3.13.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use the Python executable directly from `.venv\Scripts\python.exe`, or use a terminal whose execution policy permits activation.

## Generate the full-scale dataset

From the repository root:

```powershell
python -m src.generator --out data/generated-final --seed 20261022 --learners 20000 --courses 1000 --credentials 10000 --verifications 5000
```

The verified run produced these counts:

| Table/output | Rows |
|---|---:|
| learner | 20,000 |
| course | 1,000 |
| enrollment | 12,441 |
| issuer | 2 |
| credential_rule | 1,000 |
| completion_record | 12,441 |
| credential | 10,000 |
| verification_request | 5,000 |
| revocation | 1,000 |
| audit_event | 16,000 |
| anomaly_fixtures | 4 |
| ground_truth | 4 |

The generator exports CSV and JSON files for the tables, as well as `seed.sql`, `generation_summary.json`, and `source_manifest.json`. The manifest contains source checksums for reproducibility/integrity checks. Re-running with the same seed and same parameters should produce the same dataset content, excluding metadata that is expected to vary.

**Important:** `anomaly_fixtures` and `ground_truth` are benchmark/reference outputs, kept separate from the baseline SQL seed so that anomalous cases do not contaminate baseline records.

## Import generated SQL into a database

The following PowerShell command creates a fresh test database and imports the schema and generated seed:

```powershell
@'
import sqlite3
from pathlib import Path

schema = Path("schema.sql")
seed = Path("data/generated-final/seed.sql")
db_path = Path("data/generated-final/import_test.db")

if not schema.exists() or not seed.exists():
    raise SystemExit("Missing schema.sql or generated seed.sql")

if db_path.exists():
    db_path.unlink()

con = sqlite3.connect(db_path)
try:
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(schema.read_text(encoding="utf-8"))
    con.executescript(seed.read_text(encoding="utf-8"))
    violations = con.execute("PRAGMA foreign_key_check").fetchall()
    print("Foreign-key violations:", len(violations))
    if violations:
        print(*violations[:10], sep="\n")
        raise SystemExit("Foreign-key validation failed")
    print("SQL import and foreign-key validation: PASS")
finally:
    con.close()
'@ | python -
```

This test uses a separate `import_test.db` file. It does not replace the application's configured database.

## Run tests

```powershell
python -m unittest discover -s tests -v
python scripts/validate_anomalies.py
```

The latest recorded run passed all **9 service tests** and all **4 fixture checks**.

The service tests cover:
- Successful credential issuance.
- Duplicate issuance prevention.
- Credential-ID collision handling.
- Rejection of missing or incomplete completion records.
- Rejection of future completion timestamps.
- Missing credential verification.
- Revocation and subsequent verification.
- Detection of a changed credential payload.

The fixture validator checks:
- `ISSUED_BEFORE_COMPLETION`
- `DUPLICATE_CREDENTIAL_ID`
- `REVOKED_VERIFIES_ACTIVE`
- `ALTERED_HASH_NOT_DETECTED`

Fixture validation confirms the fixtures express the intended anomaly cases. It is not equivalent to end-to-end API tests against each fixture.

## Run the API

The project includes a FastAPI application in `src/main.py`. Install dependencies, then run:

```powershell
uvicorn src.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation when the server is running.

Use only synthetic or otherwise approved test data. Do not expose a development server or place credentials, tokens, or personal data in the public repository.

## Integrity and security notes

- SHA-256 payload hashing detects payload changes when the stored hash is trusted and recomputed during verification.
- A hash is **not** a digital signature and does not prove who issued a credential.
- The `signature_metadata` field is metadata, not a cryptographic signature.
- This project is a synthetic-data/demo implementation, not a production credential service.
- Review `docs/ASSUMPTIONS_AND_LIMITATIONS.md` before interpreting results.

## Reproducibility

Use the same Python version, seed, command-line parameters, and code revision when comparing generated data. `source_manifest.json` records file hashes for integrity verification. Do not edit generated files manually if you need reproducible checksums.

## AI-assisted development disclosure

This project includes an AI prompt-history document at `prompts/AI_PROMPT_HISTORY.md`. Keep it accurate and include the prompts used for any AI tools according to the assignment instructions. Review and understand all submitted code; be prepared to explain design choices, assumptions, tests, and limitations yourself.

## Before submission

- [ ] Confirm `schema.sql` and `src/database.py` both define the same tables, including `enrollment`.
- [ ] Run the unit tests and anomaly fixture validator from a clean checkout.
- [ ] Verify generated SQL import and `PRAGMA foreign_key_check` on a fresh database.
- [ ] Check `source_manifest.json` and reproducibility on a smaller dataset.
- [ ] Review `.gitignore` and ensure no secrets, virtual environments, temporary databases, or unnecessary large files are committed.
- [ ] Update `prompts/AI_PROMPT_HISTORY.md` with all required AI prompts and tools.
- [ ] Publish the required public GitHub repository and verify the README works from a fresh clone.
- [ ] Confirm all requirements in the official project brief are addressed.
