CREATE TABLE IF NOT EXISTS learner (
    learner_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS issuer (
    issuer_id TEXT PRIMARY KEY,
    issuer_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','INACTIVE')),
    valid_from TEXT NOT NULL,
    valid_to TEXT
);
CREATE TABLE IF NOT EXISTS course (
    course_id TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT
);
CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL REFERENCES learner(learner_id),
    course_id TEXT NOT NULL REFERENCES course(course_id),
    enrolled_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK(
        status IN ('ENROLLED', 'IN_PROGRESS', 'COMPLETED', 'WITHDRAWN')
    ),
    UNIQUE(learner_id, course_id)
);
CREATE TABLE IF NOT EXISTS credential_rule (
    rule_id TEXT PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES course(course_id),
    min_score REAL NOT NULL CHECK(min_score BETWEEN 0 AND 100),
    min_attendance REAL NOT NULL CHECK(min_attendance BETWEEN 0 AND 100),
    effective_from TEXT NOT NULL,
    effective_to TEXT
);
CREATE TABLE IF NOT EXISTS completion_record (
    completion_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL REFERENCES learner(learner_id),
    course_id TEXT NOT NULL REFERENCES course(course_id),
    completed_at TEXT,
    assessment_score REAL NOT NULL CHECK(assessment_score BETWEEN 0 AND 100),
    attendance_pct REAL NOT NULL CHECK(attendance_pct BETWEEN 0 AND 100),
    completion_status TEXT NOT NULL CHECK(completion_status IN ('IN_PROGRESS','COMPLETED','FAILED')),
    UNIQUE(learner_id, course_id)
);
CREATE TABLE IF NOT EXISTS credential (
    credential_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL REFERENCES learner(learner_id),
    course_id TEXT NOT NULL REFERENCES course(course_id),
    completion_id TEXT NOT NULL UNIQUE REFERENCES completion_record(completion_id),
    issuer_id TEXT NOT NULL REFERENCES issuer(issuer_id),
    issued_at TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    signature_metadata TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','REVOKED'))
);
CREATE TABLE IF NOT EXISTS verification_request (
    verification_id TEXT PRIMARY KEY,
    credential_id TEXT NOT NULL REFERENCES credential(credential_id),
    requested_at TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('VALID','REVOKED','TAMPERED','NOT_FOUND','INVALID'))
);
CREATE TABLE IF NOT EXISTS revocation (
    revocation_id TEXT PRIMARY KEY,
    credential_id TEXT NOT NULL REFERENCES credential(credential_id),
    revoked_at TEXT NOT NULL,
    reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_event (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action TEXT NOT NULL,
    event_at TEXT NOT NULL,
    details_json TEXT NOT NULL,
    previous_hash TEXT,
    event_hash TEXT NOT NULL UNIQUE
);
