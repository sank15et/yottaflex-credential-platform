# YottaFlex Credential Platform — Data Dictionary

This dictionary documents the baseline tables exported by `src/generator.py`. The generator uses deterministic synthetic data with default seed `20261022`. `anomaly_fixtures` and `ground_truth` are benchmark artifacts and are intentionally excluded from `seed.sql`; they are exported separately as CSV and JSON.

## Entity relationships

- `learner` 1-to-many `enrollment`
- `course` 1-to-many `enrollment`
- `learner` and `course` therefore have a many-to-many relationship through `enrollment`.
- `course` 1-to-many `credential_rule`
- `learner` + `course` 1-to-0/1 `completion_record` (unique learner/course pair)
- `completion_record` 1-to-0/1 `credential`
- `credential` 1-to-many `verification_request`
- `credential` 1-to-0/1 `revocation` in the generated baseline
- `credential` 1-to-many `audit_event` by `entity_type`/`entity_id`

## Tables and columns

### `learner`

| Column | Type / meaning | Constraints |
|---|---|---|
| `learner_id` | Synthetic learner identifier, e.g. `LRN-000001` | Primary key |
| `full_name` | Synthetic display name; names may repeat | Required |
| `email` | Synthetic email at `example.test` | Required, unique |
| `created_at` | ISO-8601 timestamp when the synthetic learner record was created | Required |

### `course`

| Column | Type / meaning | Constraints |
|---|---|---|
| `course_id` | Course identifier, e.g. `CRS-000001` | Primary key |
| `course_name` | Synthetic course title | Required |
| `effective_from` | First date the course is effective (`YYYY-MM-DD`) | Required |
| `effective_to` | Last effective date, if any | Nullable |

### `enrollment`

| Column | Type / meaning | Constraints |
|---|---|---|
| `enrollment_id` | Deterministic enrollment identifier `ENR-<learner_id>-<course_id>` | Primary key |
| `learner_id` | Learner in this enrollment | Foreign key to `learner.learner_id` |
| `course_id` | Course in this enrollment | Foreign key to `course.course_id` |
| `enrolled_at` | ISO-8601 enrollment timestamp | Required |
| `status` | Enrollment lifecycle state: `ENROLLED`, `IN_PROGRESS`, `COMPLETED`, or `WITHDRAWN` | Required; CHECK constraint |
| `(learner_id, course_id)` | Prevents duplicate enrollment for the same learner/course | Unique pair |

The generator currently creates one enrollment for each distinct learner/course pair represented in `completion_record`. A completed record has an enrollment status of `COMPLETED`, with `enrolled_at` one minute before `completed_at`; an in-progress record has status `IN_PROGRESS`.

### `issuer`

| Column | Type / meaning | Constraints |
|---|---|---|
| `issuer_id` | Credential issuer identifier, e.g. `ISS-000001` | Primary key |
| `issuer_name` | Synthetic issuer display name | Required |
| `status` | `ACTIVE` or `INACTIVE` | Required; CHECK constraint |
| `valid_from` | First date issuer is valid | Required |
| `valid_to` | Last date issuer is valid, if any | Nullable |

### `credential_rule`

| Column | Type / meaning | Constraints |
|---|---|---|
| `rule_id` | Credential rule identifier, e.g. `RUL-000001` | Primary key |
| `course_id` | Course to which the rule applies | Foreign key to `course.course_id` |
| `min_score` | Minimum assessment score required, 0–100 | Required; range CHECK |
| `min_attendance` | Minimum attendance percentage, 0–100 | Required; range CHECK |
| `effective_from` | First date the rule is effective | Required |
| `effective_to` | Last effective date, if any | Nullable |

### `completion_record`

| Column | Type / meaning | Constraints |
|---|---|---|
| `completion_id` | Completion identifier `CMP-<learner_id>-<course_id>` | Primary key |
| `learner_id` | Learner who took the course | Foreign key to `learner.learner_id` |
| `course_id` | Course attempted/completed | Foreign key to `course.course_id` |
| `completed_at` | ISO-8601 completion timestamp; blank/null for in-progress records | Nullable |
| `assessment_score` | Synthetic score from 0–100 | Required; range CHECK |
| `attendance_pct` | Synthetic attendance percentage from 0–100 | Required; range CHECK |
| `completion_status` | `IN_PROGRESS`, `COMPLETED`, or `FAILED` | Required; CHECK constraint |
| `(learner_id, course_id)` | At most one completion record per learner/course pair | Unique pair |

### `credential`

| Column | Type / meaning | Constraints |
|---|---|---|
| `credential_id` | Credential ID `CRD-<issue-year>-<sequence>` | Primary key |
| `learner_id` | Credential recipient | Foreign key to `learner.learner_id` |
| `course_id` | Credential course | Foreign key to `course.course_id` |
| `completion_id` | Completion that qualified for the credential | Foreign key to `completion_record.completion_id`; unique |
| `issuer_id` | Issuing entity | Foreign key to `issuer.issuer_id` |
| `issued_at` | ISO-8601 issuance timestamp | Required |
| `payload_json` | Canonical JSON representation of the credential payload | Required |
| `payload_hash` | SHA-256 digest of the canonical payload JSON | Required |
| `signature_metadata` | JSON metadata stating SHA-256 integrity-hash-only; not a digital signature | Required |
| `status` | `ACTIVE` or `REVOKED` | Required; CHECK constraint |

### `verification_request`

| Column | Type / meaning | Constraints |
|---|---|---|
| `verification_id` | Verification identifier `VER-<request-year>-<sequence>` | Primary key |
| `credential_id` | Credential being checked | Foreign key to `credential.credential_id` |
| `requested_at` | ISO-8601 verification timestamp | Required |
| `result` | Baseline result `VALID` or `REVOKED`; service may also produce `TAMPERED`, `NOT_FOUND`, or `INVALID` as allowed by schema | Required; CHECK constraint |

### `revocation`

| Column | Type / meaning | Constraints |
|---|---|---|
| `revocation_id` | Revocation identifier `REV-<credential_id>-01` | Primary key |
| `credential_id` | Revoked credential | Foreign key to `credential.credential_id` |
| `revoked_at` | ISO-8601 revocation timestamp, after issuance | Required |
| `reason` | Synthetic revocation reason | Required |

### `audit_event`

| Column | Type / meaning | Constraints |
|---|---|---|
| `event_id` | Sequential audit event identifier `AUD-<sequence>` | Primary key |
| `entity_type` | Entity type associated with event, e.g. `credential` | Required |
| `entity_id` | Identifier of the related entity | Required |
| `action` | Synthetic action such as `CREDENTIAL_ISSUED`, `CREDENTIAL_VERIFIED`, or `CREDENTIAL_REVOKED` | Required |
| `event_at` | ISO-8601 event timestamp | Required |
| `details_json` | Canonical JSON details for the event | Required |
| `previous_hash` | Hash of preceding event; null for first event | Nullable |
| `event_hash` | SHA-256 hash of the event contents including `previous_hash` | Required, unique |

### `anomaly_fixtures` (benchmark-only; not inserted into baseline SQL)

| Column | Type / meaning |
|---|---|
| `fixture_id` | Fixture identifier, `ANOM-001` through `ANOM-004` |
| `issue_type` | One of the four required anomaly classes |
| `entity_id`, `credential_id` | Entity/credential the fixture targets |
| Other columns | Scenario-specific values such as timestamps, attempted operation, tampered payload, stored hash, and expected detection |

Fixture columns vary by anomaly type; CSV columns are the union of keys across all fixture records.

### `ground_truth` (benchmark-only; not inserted into baseline SQL)

| Column | Type / meaning |
|---|---|
| `anomaly_id` | Ground-truth label ID |
| `issue_type` | Expected anomaly class |
| `entity_id` | Entity targeted by the fixture |
| `expected_detection` | Expected application behavior for the anomaly |
| `description` | Human-readable explanation of the labeled condition |

## Lifecycle and integrity notes

- Credential issuance must occur after successful completion and within the issuer/course/rule validity windows.
- Revocation must occur after issuance; subsequent verification should return `REVOKED`.
- Verification requests in the clean baseline occur after issuance and, for revoked credentials, after revocation.
- Payload hashes detect payload changes only if the expected hash is trusted and protected. SHA-256 hashing alone does not authenticate the issuer and is not a digital signature.
- Audit hashes form a tamper-evident linked sequence for the generated event ordering; this is a synthetic event history, not evidence that the live API performed those operations.
- All names, email addresses, courses, and activity are synthetic.
