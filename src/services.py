
"""Credential domain services."""

import hashlib
import json
from datetime import datetime, timezone, date

from .database import connect


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def canonical_json(obj):
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _audit(conn, entity_type, entity_id, action, details):
    previous = conn.execute(
        "SELECT event_hash FROM audit_event ORDER BY rowid DESC LIMIT 1"
    ).fetchone()

    prev_hash = previous["event_hash"] if previous else None

    count = conn.execute(
        "SELECT COUNT(*) AS n FROM audit_event"
    ).fetchone()["n"]

    event = {
        "event_id": f"AUD-{count + 1:09d}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "event_at": now_iso(),
        "details_json": canonical_json(details),
        "previous_hash": prev_hash,
    }

    event["event_hash"] = sha256_text(canonical_json(event))

    conn.execute(
        """
        INSERT INTO audit_event
        (
            event_id, entity_type, entity_id, action,
            event_at, details_json, previous_hash, event_hash
        )
        VALUES
        (
            :event_id, :entity_type, :entity_id, :action,
            :event_at, :details_json, :previous_hash, :event_hash
        )
        """,
        event,
    )


def create_learner(learner_id, full_name, email):
    with connect() as conn:
        conn.execute(
            "INSERT INTO learner VALUES (?,?,?,?)",
            (learner_id, full_name, email, now_iso()),
        )

    return {"learner_id": learner_id}


def create_course(
    course_id,
    course_name,
    effective_from=None,
    effective_to=None,
):
    with connect() as conn:
        conn.execute(
            "INSERT INTO course VALUES (?,?,?,?)",
            (
                course_id,
                course_name,
                effective_from or date.today().isoformat(),
                effective_to,
            ),
        )

    return {"course_id": course_id}


def create_issuer(
    issuer_id,
    issuer_name,
    valid_from=None,
    valid_to=None,
):
    with connect() as conn:
        conn.execute(
            "INSERT INTO issuer VALUES (?,?,?,?,?)",
            (
                issuer_id,
                issuer_name,
                "ACTIVE",
                valid_from or date.today().isoformat(),
                valid_to,
            ),
        )

    return {"issuer_id": issuer_id}


def create_rule(
    rule_id,
    course_id,
    min_score,
    min_attendance,
    effective_from=None,
    effective_to=None,
):
    with connect() as conn:
        conn.execute(
            "INSERT INTO credential_rule VALUES (?,?,?,?,?,?)",
            (
                rule_id,
                course_id,
                min_score,
                min_attendance,
                effective_from or date.today().isoformat(),
                effective_to,
            ),
        )

    return {"rule_id": rule_id}


def create_completion(
    completion_id,
    learner_id,
    course_id,
    score,
    attendance,
    status,
    completed_at=None,
):
    if status not in {"IN_PROGRESS", "COMPLETED", "FAILED"}:
        raise ValueError("Invalid completion status")

    with connect() as conn:
        conn.execute(
            "INSERT INTO completion_record VALUES (?,?,?,?,?,?,?)",
            (
                completion_id,
                learner_id,
                course_id,
                completed_at,
                score,
                attendance,
                status,
            ),
        )

    return {"completion_id": completion_id}


def issue_credential(learner_id, course_id, issuer_id):
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")

        today = date.today().isoformat()

        learner = conn.execute(
            "SELECT * FROM learner WHERE learner_id = ?",
            (learner_id,),
        ).fetchone()

        course = conn.execute(
            "SELECT * FROM course WHERE course_id = ?",
            (course_id,),
        ).fetchone()

        issuer = conn.execute(
            "SELECT * FROM issuer WHERE issuer_id = ?",
            (issuer_id,),
        ).fetchone()

        if not learner or not course or not issuer:
            raise ValueError("Learner, course, or issuer not found")

        if (
            issuer["status"] != "ACTIVE"
            or issuer["valid_from"] > today
            or (
                issuer["valid_to"]
                and issuer["valid_to"] < today
            )
        ):
            raise ValueError(
                "Issuer is inactive or outside its validity period"
            )

        if (
            course["effective_from"] > today
            or (
                course["effective_to"]
                and course["effective_to"] < today
            )
        ):
            raise ValueError("Course is outside its effective period")

        rule = conn.execute(
            """
            SELECT *
            FROM credential_rule
            WHERE course_id = ?
              AND effective_from <= ?
              AND (effective_to IS NULL OR effective_to >= ?)
            ORDER BY effective_from DESC
            LIMIT 1
            """,
            (course_id, today, today),
        ).fetchone()

        if not rule:
            raise ValueError("No effective credential rule")

        completion = conn.execute(
            """
            SELECT *
            FROM completion_record
            WHERE learner_id = ? AND course_id = ?
            """,
            (learner_id, course_id),
        ).fetchone()

        if not completion:
            raise ValueError("Completion record not found")

        if (
            completion["completion_status"] != "COMPLETED"
            or not completion["completed_at"]
        ):
            raise ValueError("Course completion requirements not met")

        issued_at = now_iso()

        # Prevent issuance if the completion timestamp is in the future.
        if completion["completed_at"] > issued_at:
            raise ValueError("Completion timestamp is in the future")

        if completion["assessment_score"] < rule["min_score"]:
            raise ValueError("Minimum assessment score not met")

        if completion["attendance_pct"] < rule["min_attendance"]:
            raise ValueError("Minimum attendance not met")

        existing_completion = conn.execute(
            "SELECT 1 FROM credential WHERE completion_id = ?",
            (completion["completion_id"],),
        ).fetchone()

        if existing_completion:
            raise ValueError(
                "Credential already issued for this completion"
            )

        # Find an unused ID instead of assuming COUNT(*) + 1 is available.
        year = datetime.now(timezone.utc).year

        count = conn.execute(
            "SELECT COUNT(*) AS n FROM credential"
        ).fetchone()["n"]

        sequence = count + 1

        while True:
            credential_id = f"CRD-{year}-{sequence:06d}"

            existing_id = conn.execute(
                "SELECT 1 FROM credential WHERE credential_id = ?",
                (credential_id,),
            ).fetchone()

            if existing_id is None:
                break

            sequence += 1

        payload = {
            "credential_id": credential_id,
            "learner_id": learner_id,
            "course_id": course_id,
            "completion_id": completion["completion_id"],
            "issuer_id": issuer_id,
            "rule_id": rule["rule_id"],
            "issued_at": issued_at,
        }

        payload_json = canonical_json(payload)
        payload_hash = sha256_text(payload_json)

        sig_meta = canonical_json({
            "algorithm": "SHA-256",
            "type": "integrity-hash-only",
            "is_digital_signature": False,
        })

        conn.execute(
            """
            INSERT INTO credential
            (
                credential_id, learner_id, course_id, completion_id,
                issuer_id, issued_at, payload_json, payload_hash,
                signature_metadata, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
            """,
            (
                credential_id,
                learner_id,
                course_id,
                completion["completion_id"],
                issuer_id,
                issued_at,
                payload_json,
                payload_hash,
                sig_meta,
            ),
        )

        _audit(
            conn,
            "Credential",
            credential_id,
            "ISSUED",
            {"payload_hash": payload_hash},
        )

        return {
            "credential_id": credential_id,
            "status": "ACTIVE",
            "payload_hash": payload_hash,
        }


def verify_credential(credential_id):
    with connect() as conn:
        cred = conn.execute(
            "SELECT * FROM credential WHERE credential_id = ?",
            (credential_id,),
        ).fetchone()

        result = "NOT_FOUND"

        if cred:
            expected_hash = sha256_text(cred["payload_json"])

            # Integrity check takes priority over the status check.
            if expected_hash != cred["payload_hash"]:
                result = "TAMPERED"
            elif cred["status"] == "REVOKED":
                result = "REVOKED"
            else:
                result = "VALID"

            count = conn.execute(
                "SELECT COUNT(*) AS n FROM verification_request"
            ).fetchone()["n"]

            conn.execute(
                "INSERT INTO verification_request VALUES (?,?,?,?)",
                (
                    f"VER-{datetime.now(timezone.utc).year}-{count + 1:06d}",
                    credential_id,
                    now_iso(),
                    result,
                ),
            )

            _audit(
                conn,
                "Credential",
                credential_id,
                "VERIFIED",
                {"result": result},
            )

        return {
            "credential_id": credential_id,
            "result": result,
        }


def revoke_credential(credential_id, reason):
    if not reason.strip():
        raise ValueError("Revocation reason is required")

    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")

        cred = conn.execute(
            "SELECT * FROM credential WHERE credential_id = ?",
            (credential_id,),
        ).fetchone()

        if not cred:
            raise ValueError("Credential not found")

        if cred["status"] == "REVOKED":
            raise ValueError("Credential is already revoked")

        count = conn.execute(
            "SELECT COUNT(*) AS n FROM revocation WHERE credential_id = ?",
            (credential_id,),
        ).fetchone()["n"]

        revocation_id = f"REV-{credential_id}-{count + 1:02d}"
        revoked_at = now_iso()

        conn.execute(
            "UPDATE credential SET status = 'REVOKED' WHERE credential_id = ?",
            (credential_id,),
        )

        conn.execute(
            "INSERT INTO revocation VALUES (?,?,?,?)",
            (revocation_id, credential_id, revoked_at, reason),
        )

        _audit(
            conn,
            "Credential",
            credential_id,
            "REVOKED",
            {
                "revocation_id": revocation_id,
                "reason": reason,
            },
        )

        return {
            "credential_id": credential_id,
            "revocation_id": revocation_id,
            "status": "REVOKED",
        }
