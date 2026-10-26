# AI Prompt History — YottaFlex Credential Platform

## 1. Project Information

- **Project:** YottaFlex Credential Platform
- **AI tool used:** ChatGPT
- **Model:** Record the model shown in each relevant conversation.
- **Development period:** October 2026, plus earlier dates for relevant conversations.
- **Purpose:** To disclose AI assistance used during project development, including prompts, generated suggestions or code, modifications, and validation.

## 2. Project Requirements and Planning

### Entry 1 — Requirements analysis

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** Requirements breakdown, entity identification, implementation planning, or project structure, as applicable.
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Compared the proposed plan against the official project brief.

## 3. Database Schema and Data Model

### Entry 2 — Database design

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Record actual schema or relationship suggestions used.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Schema inspection, SQL import, and foreign-key checks, as applicable.

### Entry 3 — Enrollment bridge table

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** Enrollment table design and generator integration, if applicable.
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Confirmed 65 enrollment IDs and 65 unique learner-course pairs in the smoke test. The SQL import also passed with zero foreign-key violations.

## 4. Python Service Implementation

### Entry 4 — Credential issuance

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Identify the actual service implementation or suggestions used.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Service unit tests, including successful issuance, duplicate prevention, and completion-timestamp validation.

### Entry 5 — Credential verification and payload integrity

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Record actual verification and hash-checking assistance.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Unit test for tampered payload detection and missing credential verification.

### Entry 6 — Credential revocation

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Record actual revocation-related assistance.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Tests for revocation and subsequent verification.

## 5. Synthetic Data Generator

### Entry 7 — Deterministic data generation

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Record generator code, data-volume logic, or export logic actually used.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Ran the generator with seed `20261022` and checked generated row counts.

### Entry 8 — CSV, JSON, and SQL exports

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Identify export implementation used.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Checked the generated output files and imported `seed.sql` into a fresh SQLite database.

## 6. Anomaly Fixtures and Ground Truth

### Entry 9 — Required anomaly cases

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Record actual fixture or validator assistance.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** `python scripts/validate_anomalies.py` reported 4/4 fixture checks passed.

The four fixture cases are:
1. `ISSUED_BEFORE_COMPLETION`
2. `DUPLICATE_CREDENTIAL_ID`
3. `REVOKED_VERIFIES_ACTIVE`
4. `ALTERED_HASH_NOT_DETECTED`

The fixture validator checks the intended fixture characteristics. It does not by itself prove all four cases have been exercised end-to-end through the application.

## 7. Testing and Validation

### Entry 10 — Unit and API tests

- **AI tool:** ChatGPT.
- **Exact prompt:** Original prompt wording not yet recovered; see completeness disclosure.
- **AI assistance:** Testing strategy and implementation/debugging assistance for service and API behavior, where applicable.
- **Validation:** `python -m unittest discover -s tests -v` passed all 14 tests in the recorded run. A non-fatal Starlette/httpx deprecation warning was observed.
- **Limitations:** This result applies to the recorded test run; it does not establish that every possible edge case has been tested.

### Entry 11 — Data lifecycle and foreign-key checks

- **AI tool:** ChatGPT.
- **Exact prompt:** Original prompt wording not yet recovered; see completeness disclosure.
- **AI assistance:** Validation workflow and troubleshooting assistance, where applicable.
- **Validation:** The full-scale database foreign-key check returned no violations. `scripts/validate_lifecycle.py` reported that no credentials were issued before completion. The anomaly fixture validator reported 4/4 fixture checks passed.
- **Limitations:** The four fixture checks validate intended fixture characteristics; they do not prove end-to-end detection of every anomaly class.

## 8. Documentation and GitHub

### Entry 12 — README and assumptions

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** README, data dictionary, and assumptions/limitations documentation, where applicable.
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Reviewed file contents and checked documented commands against the recorded test results.

### Entry 13 — Git and GitHub setup

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** Git initialization, `.gitignore` review, commit, remote setup, and push instructions.
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** Initial commit `5c04ebb` was created, and the `main` branch was pushed to the configured GitHub remote.

### Entry 14 — Deterministic dataset reproducibility

- **AI tool:** ChatGPT.
- **Date/time:** 26 October 2026; consult the original conversation for the exact prompt timestamp.
- **Exact prompt:** Original prompt wording not yet recovered; see completeness disclosure.
- **AI assistance:** Guidance for comparing two generated datasets and documenting reproducibility.
- **Configuration:** Seed `20261022`; 20,000 learners; 1,000 courses; 10,000 credentials; 5,000 verification requests.
- **Validation:** Generated datasets in `data/repro-run-1` and `data/repro-run-2` using identical parameters. Compared row counts and SHA-256 hashes of corresponding files. All 26 corresponding files were identical, and all generated entity counts matched.
- **Limitations:** This establishes reproducibility for the tested seed, configuration, and code revision; it does not establish identical results for every possible configuration or environment.


## 9. Other AI Tools

For every additional AI tool used, record:
- Tool and model.
- Date/time.
- Exact prompt submitted.
- Output or code used.
- Changes made.
- Validation performed.

Do not omit tools simply because their output was not used in the final implementation if the assignment requires all prompts to be disclosed.

## 10. Author Review and Responsibility

I reviewed the generated code and test results to the extent recorded in this project history. I am responsible for understanding the implementation, verifying the claims in the documentation, and explaining the design decisions, assumptions, trade-offs, and limitations.

## 11. Completeness Status

**Status: Partial — original prompts still need recovery.**

This document is a disclosure framework and development summary, not a complete verbatim transcript of every AI interaction. The original prompt text and some dates/model details were not recoverable from the files included in this submission. Do not treat placeholder entries as exact prompts or as evidence that every listed prompt was submitted. Before submission, recover and insert original prompts from the relevant conversation histories or AI tool records if the assignment requires verbatim prompt disclosure. If they cannot be recovered, disclose that limitation honestly rather than fabricating prompt text.
