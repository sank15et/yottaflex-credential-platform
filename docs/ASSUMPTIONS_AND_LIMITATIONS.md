# Assumptions and Limitations

## Scope

This project is a Python/SQLite demonstration of a credential issuance lifecycle and a deterministic synthetic-data generator. It is not a production credentialing platform.

## Data-generation assumptions

- The full-scale generator was run with seed `20261022`.
- The recorded full-scale counts are 20,000 learners, 1,000 courses, 12,441 enrollment records, 2 issuers, 1,000 credential rules, 12,441 completion records, 10,000 credentials, 5,000 verification requests, 1,000 revocations, and 16,000 audit events.
- Four anomaly fixtures and four corresponding ground-truth records are exported separately from baseline records.
- Enrollment records are generated for learner/course pairs represented by generated completion records. Therefore, the enrollment count follows the completion-record count in this generated dataset; it should not be interpreted as the total number of all possible learner/course enrollments.
- Synthetic data is for testing and demonstration. Names, dates, scores, statuses, and relationships do not represent real people or real credentials.
- Reproducibility depends on using the same generator code revision, seed, parameters, and compatible runtime.

## Integrity and lifecycle validation

The full-scale generated dataset was imported into a fresh SQLite database and validated. The recorded full-scale checks reported:
- SQL seed import passed.
- `PRAGMA foreign_key_check` reported zero violations.
- No credentials were issued before completion.
- Issuance timestamps fell within issuer validity periods.
- Revocation timestamps were not earlier than issuance.
- Verification requests were not earlier than credential issuance.
- No duplicate credential IDs or duplicate learner-course enrollment pairs were found.

The standalone lifecycle validator can be run against a database path, for example `python scripts/validate_lifecycle.py data/generated-final/full_validation.db`. The generated database itself is a local artifact and may not be included in a clean source-only repository or ZIP; if absent, import `data/generated-final/seed.sql` into a fresh database before running database checks.

## Anomaly coverage

The fixture validator reports all four required anomaly fixtures as passing:
1. `ISSUED_BEFORE_COMPLETION`
2. `DUPLICATE_CREDENTIAL_ID`
3. `REVOKED_VERIFIES_ACTIVE`
4. `ALTERED_HASH_NOT_DETECTED`

This script validates the intended characteristics of the fixtures. It does not, by itself, prove that the API or service layer detects each fixture end-to-end. The unit tests separately demonstrate service behavior for duplicate issuance/collision, invalid completion timing, revocation, and payload tampering. Add dedicated integration tests that feed each anomaly fixture through the relevant service/API path if the project requirements demand end-to-end anomaly detection.

## Hashing and signatures

- Credential payload integrity uses SHA-256 over canonicalized payload content.
- SHA-256 detects a mismatch only when the verifier compares the recomputed hash against a trusted stored hash.
- A plain hash is not a digital signature. If an attacker can alter both the payload and its stored hash, a hash comparison alone cannot establish authenticity.
- `signature_metadata` is descriptive metadata and must not be presented as a cryptographic signature.
- No claim of public-key signing, issuer identity proof, or external trust registry is made.

## Database and API limitations

- SQLite is suitable for a local demonstration and automated tests; concurrent production workloads, access control, backups, monitoring, and operational recovery are outside the demonstrated scope.
- The API is a local development service. Production deployment, authentication, authorization, rate limiting, transport security, and privacy controls require separate implementation and testing.
- Foreign-key checks validate referential integrity, not every business rule.
- Unit tests cover selected service paths. They are not a complete integration, load, security, or penetration test suite.
- The local application database and generated dataset are separate artifacts. Importing `seed.sql` into a new test database does not automatically update the application's configured database.

## Submission and reproducibility

- Keep the AI prompt history accurate and complete according to the project instructions.
- Verify the public repository from a fresh clone and ensure setup/test instructions work.
- Avoid committing API keys, passwords, personal data, virtual environments, temporary test databases, or large generated files unless the submission instructions explicitly require them.
