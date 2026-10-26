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

### Entry 10 — Unit tests

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Identify test code or testing advice actually used.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** `python -m unittest discover -s tests -v` passed all 9 service tests in the recorded run.

### Entry 11 — Data lifecycle and foreign-key checks

- **Date/time:** [Recover from original conversation]
- **Tool/model:** ChatGPT / [model]
- **Exact prompt submitted:** [Paste the original prompt verbatim.]
- **AI output or code used:** [Identify the actual validation scripts or SQL queries used.]
- **What I changed or rejected:** [Describe actual changes.]
- **How I validated it:** The smoke-test database had zero foreign-key violations and zero violations across the four tested lifecycle rules. Run the same checks against the full-scale dataset before claiming full-scale validation.

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

**Status: In progress.**

This log is not complete until all required original prompts have been recovered from the relevant conversation histories or AI tool records and entered verbatim. The section headings and descriptions above are a recording framework, not evidence that every listed prompt was actually submitted.
