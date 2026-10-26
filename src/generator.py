"""Deterministic synthetic data generator for the YottaFlex credential platform.

Generates CSV/JSON/SQLite SQL seed exports and separate anomaly ground truth.
All names and email addresses are synthetic. Fixed seed makes generation reproducible.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, random, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED_DEFAULT = 20261022

def stable_hash(obj):
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def dt_string(dt):
    return dt.replace(microsecond=0).isoformat()

def make_rows(seed=SEED_DEFAULT, learners_n=20000, courses_n=1000,
              credentials_n=10000, verifications_n=5000):
    rng = random.Random(seed)
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 10, 1, tzinfo=timezone.utc)
    span = int((end-start).total_seconds())
    def timestamp():
        return dt_string(start + timedelta(seconds=rng.randint(0, span)))
    names = ["Aarav Sharma", "Asha Patil", "Rohan Kulkarni", "Priya Shah",
             "Neha Joshi", "Arjun Desai", "Isha Mehta", "Duplicate Name"]
    learners = []
    for i in range(1, learners_n+1):
        # Duplicate display names are intentional; IDs, not names, identify learners.
        name = names[(i-1) % len(names)]
        learners.append({"learner_id": f"LRN-{i:06d}", "full_name": name,
                         "email": f"learner{i:06d}@example.test", "created_at": timestamp()})
    courses = [{"course_id": f"CRS-{i:06d}", "course_name": f"Course {i:04d}",
                "effective_from": "2024-01-01", "effective_to": ""}
               for i in range(1, courses_n+1)]
    issuers = [
        {"issuer_id": "ISS-000001", "issuer_name": "Synthetic Issuer Alpha",
         "status": "ACTIVE", "valid_from": "2024-01-01", "valid_to": ""},
        {"issuer_id": "ISS-000002", "issuer_name": "Synthetic Issuer Beta",
         "status": "ACTIVE", "valid_from": "2025-01-01", "valid_to": ""},
    ]
    rules = []
    for i, course in enumerate(courses, 1):
        rules.append({"rule_id": f"RUL-{i:06d}", "course_id": course["course_id"],
                      "min_score": 70, "min_attendance": 80,
                      "effective_from": "2024-01-01", "effective_to": ""})
    # Select unique learner/course pairs without materializing the full Cartesian
    # product. random.sample(range(...), k) is memory-efficient for this use case.
    pair_count = learners_n * courses_n
    if learners_n < 1 or courses_n < 1:
        raise ValueError("Learner and course counts must both be positive")
    if credentials_n < 1:
        raise ValueError("Credential count must be positive")
    if credentials_n > pair_count:
        raise ValueError("Credential count exceeds unique learner/course pairs")
    selected_pair_indexes = rng.sample(range(pair_count), credentials_n)
    selected = [(pair_index // courses_n, pair_index % courses_n)
                for pair_index in selected_pair_indexes]
    completions, credentials = [], []
    for idx, (li, ci) in enumerate(selected, 1):
        learner = learners[li]; course = courses[ci]
        completed_at = timestamp()
        score = rng.randint(70, 100)
        attendance = rng.randint(80, 100)
        completion_id = f"CMP-{learner['learner_id']}-{course['course_id']}"
        completions.append({"completion_id": completion_id, "learner_id": learner["learner_id"],
                            "course_id": course["course_id"], "completed_at": completed_at,
                            "assessment_score": score, "attendance_pct": attendance,
                            "completion_status": "COMPLETED"})
        issued_at_dt = datetime.fromisoformat(completed_at) + timedelta(minutes=rng.randint(1, 10080))
        issued_at = dt_string(issued_at_dt)
        # Issuer Beta is only valid from 2025-01-01. Select it only for
        # credentials issued on/after that date; Alpha is valid from 2024.
        issuer_id = (
            "ISS-000002"
            if issued_at_dt.date() >= datetime(2025, 1, 1).date() and idx % 4 == 0
            else "ISS-000001"
        )
        credential_id = f"CRD-{issued_at_dt.year}-{idx:06d}"
        payload = {"credential_id": credential_id, "learner_id": learner["learner_id"],
                   "course_id": course["course_id"], "completion_id": completion_id,
                   "issuer_id": issuer_id, "issued_at": issued_at}
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        credentials.append({"credential_id": credential_id, "learner_id": learner["learner_id"],
                            "course_id": course["course_id"], "completion_id": completion_id,
                            "issuer_id": issuer_id, "issued_at": issued_at,
                            "payload_json": payload_json, "payload_hash": stable_hash(payload),
                            "signature_metadata": json.dumps({"algorithm":"SHA-256",
                                "type":"integrity-hash-only","is_digital_signature":False},
                                sort_keys=True), "status": "ACTIVE"})
    # Additional incomplete course records, separate from credential-bearing pairs.
    completed_pairs = {(x["learner_id"], x["course_id"]) for x in completions}
    for learner in learners:
        if rng.random() < 0.12:
            course = courses[rng.randrange(len(courses))]
            pair = (learner["learner_id"], course["course_id"])
            if pair in completed_pairs:
                continue
            completions.append({"completion_id": f"CMP-{pair[0]}-{pair[1]}",
                "learner_id": pair[0], "course_id": pair[1], "completed_at": "",
                "assessment_score": rng.randint(0, 69), "attendance_pct": rng.randint(0, 79),
                "completion_status": "IN_PROGRESS"})
            completed_pairs.add(pair)
    # Revocations are derived as a deterministic subset, not random statuses.
    revocations = []
    for i, credential in enumerate(credentials, 1):
        if i % 10 == 0:
            credential["status"] = "REVOKED"
            revocations.append({"revocation_id": f"REV-{credential['credential_id']}-01",
                "credential_id": credential["credential_id"],
                "revoked_at": dt_string(datetime.fromisoformat(credential["issued_at"]) + timedelta(days=1)),
                "reason": "Synthetic policy review"})
    verification_requests = []
    if credentials_n < 1 and verifications_n > 0:
        raise ValueError("At least one credential is required for verification requests")
    if verifications_n < 0:
        raise ValueError("Verification count cannot be negative")
    for i in range(1, verifications_n+1):
        credential = credentials[(i * 7 - 1) % len(credentials)]
        issued_dt = datetime.fromisoformat(credential["issued_at"])
        revoked_row = next((r for r in revocations if r["credential_id"] == credential["credential_id"]), None)
        earliest = datetime.fromisoformat(revoked_row["revoked_at"]) if revoked_row else issued_dt
        requested_dt = earliest + timedelta(minutes=rng.randint(1, 100000))
        result = "REVOKED" if credential["status"] == "REVOKED" else "VALID"
        verification_requests.append({"verification_id": f"VER-{requested_dt.year}-{i:06d}",
            "credential_id": credential["credential_id"], "requested_at": dt_string(requested_dt), "result": result})
    # Ground truth labels map to concrete, isolated fixture records. Fixtures are
    # exported separately and intentionally excluded from clean baseline SQL inserts.
    # Pick two real baseline credentials for the duplicate-ID, revoked-status and
    # altered-payload scenarios. The fixtures are separate from clean baseline rows.
    if credentials_n < 10:
        raise ValueError("At least 10 credentials are required for the four anomaly fixtures")
    revoked_credential = next(c for c in credentials if c["status"] == "REVOKED")
    tamper_credential = next(c for c in credentials if c["status"] == "ACTIVE")
    tampered_payload = json.loads(tamper_credential["payload_json"])
    tampered_payload["learner_id"] = "LRN-TAMPERED"
    anomaly_fixtures = [
        {"fixture_id":"ANOM-001","issue_type":"ISSUED_BEFORE_COMPLETION",
         "entity_id":"CRD-ANOM-000001","credential_id":"CRD-ANOM-000001",
         "completion_id":"CMP-ANOM-001","completed_at":"2026-05-10T12:00:00+00:00",
         "issued_at":"2026-05-09T12:00:00+00:00","expected_detection":"REJECT_OR_FLAG"},
        {"fixture_id":"ANOM-002","issue_type":"DUPLICATE_CREDENTIAL_ID",
         "entity_id":credentials[0]["credential_id"],"credential_id":credentials[0]["credential_id"],
         "attempt":"INSERT_DUPLICATE_ID","expected_detection":"REJECT_DUPLICATE"},
        {"fixture_id":"ANOM-003","issue_type":"REVOKED_VERIFIES_ACTIVE",
         "entity_id":revoked_credential["credential_id"],"credential_id":revoked_credential["credential_id"],
         "actual_status":revoked_credential["status"],"injected_verification_result":"ACTIVE",
         "expected_detection":"MUST_RETURN_REVOKED"},
        {"fixture_id":"ANOM-004","issue_type":"ALTERED_HASH_NOT_DETECTED",
         "entity_id":tamper_credential["credential_id"],"credential_id":tamper_credential["credential_id"],
         "original_payload_json":tamper_credential["payload_json"],
         "tampered_payload_json":json.dumps(tampered_payload,sort_keys=True,separators=(",",":")),
         "stored_payload_hash":tamper_credential["payload_hash"],
         "expected_detection":"MUST_FLAG_TAMPERED"}
    ]
    ground_truth = [
        {"anomaly_id":"ANOM-001","issue_type":"ISSUED_BEFORE_COMPLETION",
         "entity_id":"CRD-ANOM-000001","expected_detection":"REJECT_OR_FLAG",
         "description":"Concrete fixture has issued_at earlier than completed_at."},
        {"anomaly_id":"ANOM-002","issue_type":"DUPLICATE_CREDENTIAL_ID",
         "entity_id":credentials[0]["credential_id"],"expected_detection":"REJECT_DUPLICATE",
         "description":"Concrete fixture attempts to insert an existing credential ID."},
        {"anomaly_id":"ANOM-003","issue_type":"REVOKED_VERIFIES_ACTIVE",
         "entity_id":revoked_credential["credential_id"],"expected_detection":"MUST_RETURN_REVOKED",
         "description":"Concrete fixture supplies ACTIVE as the wrong verification result for a revoked credential."},
        {"anomaly_id":"ANOM-004","issue_type":"ALTERED_HASH_NOT_DETECTED",
         "entity_id":tamper_credential["credential_id"],"expected_detection":"MUST_FLAG_TAMPERED",
         "description":"Concrete fixture changes payload data while retaining the original stored hash."}
    ]
    # Validate baseline lifecycle invariants before exporting.
    completion_by_id = {row["completion_id"]: row for row in completions}
    issuer_by_id = {row["issuer_id"]: row for row in issuers}
    credential_by_id = {row["credential_id"]: row for row in credentials}
    revocation_by_credential = {row["credential_id"]: row for row in revocations}
    credential_ids = [row["credential_id"] for row in credentials]
    if len(credential_ids) != len(set(credential_ids)):
        raise AssertionError("Generated duplicate credential IDs")
    for credential in credentials:
        completion = completion_by_id[credential["completion_id"]]
        if not completion["completed_at"]:
            raise AssertionError("Credential references a completion without completed_at")
        if datetime.fromisoformat(credential["issued_at"]) <= datetime.fromisoformat(completion["completed_at"]):
            raise AssertionError("Credential issue time must follow completion time")
        issuer = issuer_by_id[credential["issuer_id"]]
        issued_date = datetime.fromisoformat(credential["issued_at"]).date()
        if issued_date.isoformat() < issuer["valid_from"]:
            raise AssertionError("Credential issue date precedes issuer validity")
        if issuer["valid_to"] and issued_date.isoformat() > issuer["valid_to"]:
            raise AssertionError("Credential issue date exceeds issuer validity")
    for revocation in revocations:
        credential = credential_by_id[revocation["credential_id"]]
        if datetime.fromisoformat(revocation["revoked_at"]) <= datetime.fromisoformat(credential["issued_at"]):
            raise AssertionError("Revocation must occur after issuance")
    for request in verification_requests:
        credential = credential_by_id[request["credential_id"]]
        if datetime.fromisoformat(request["requested_at"]) < datetime.fromisoformat(credential["issued_at"]):
            raise AssertionError("Verification cannot precede issuance")
        revoked = revocation_by_credential.get(credential["credential_id"])
        if revoked and datetime.fromisoformat(request["requested_at"]) < datetime.fromisoformat(revoked["revoked_at"]):
            raise AssertionError("Verification of revoked credential cannot precede revocation in this baseline")

    # Bridge table: one enrollment per learner/course pair represented by a
    # completion record. Completed enrollments precede their completion time.
    enrollment_by_pair = {}
    for completion in completions:
        pair = (completion["learner_id"], completion["course_id"])
        if completion["completion_status"] == "COMPLETED" and completion["completed_at"]:
            completed_dt = datetime.fromisoformat(completion["completed_at"])
            enrolled_at = dt_string(completed_dt - timedelta(minutes=1))
            enrollment_status = "COMPLETED"
        else:
            enrolled_at = timestamp()
            enrollment_status = "IN_PROGRESS"

        enrollment_by_pair[pair] = {
            "enrollment_id": f"ENR-{completion['learner_id']}-{completion['course_id']}",
            "learner_id": completion["learner_id"],
            "course_id": completion["course_id"],
            "enrolled_at": enrolled_at,
            "status": enrollment_status,
        }

    enrollments = list(enrollment_by_pair.values())

    # Generate a deterministic synthetic audit trail for baseline operations.
    # These rows represent the synthetic dataset's events; they are not claims
    # that the live API performed these actions.
    audit_actions = []

    for credential in credentials:
        audit_actions.append({
            "entity_type": "credential",
            "entity_id": credential["credential_id"],
            "action": "CREDENTIAL_ISSUED",
            "event_at": credential["issued_at"],
            "details": {
                "status_at_issuance": "ACTIVE",
                "learner_id": credential["learner_id"],
                "course_id": credential["course_id"],
            },
        })

    for request in verification_requests:
        audit_actions.append({
            "entity_type": "credential",
            "entity_id": request["credential_id"],
            "action": "CREDENTIAL_VERIFIED",
            "event_at": request["requested_at"],
            "details": {
                "verification_id": request["verification_id"],
                "result": request["result"],
            },
        })

    for revocation in revocations:
        audit_actions.append({
            "entity_type": "credential",
            "entity_id": revocation["credential_id"],
            "action": "CREDENTIAL_REVOKED",
            "event_at": revocation["revoked_at"],
            "details": {
                "revocation_id": revocation["revocation_id"],
                "reason": revocation["reason"],
            },
        })

    # Stable ordering ensures repeatable event IDs and hash-chain values.
    audit_actions.sort(
        key=lambda event: (
            event["event_at"],
            event["entity_type"],
            event["entity_id"],
            event["action"],
        )
    )

    audit_events = []
    previous_hash = None

    for index, action in enumerate(audit_actions, start=1):
        details_json = json.dumps(
            action["details"],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        event_content = {
            "event_id": f"AUD-{index:09d}",
            "entity_type": action["entity_type"],
            "entity_id": action["entity_id"],
            "action": action["action"],
            "event_at": action["event_at"],
            "details_json": details_json,
            "previous_hash": previous_hash,
        }
        event_hash = stable_hash(event_content)
        audit_events.append({
            **event_content,
            "event_hash": event_hash,
        })
        previous_hash = event_hash

    return {
        "learner": learners,
        "course": courses,
        "enrollment": enrollments,
        "issuer": issuers,
        "credential_rule": rules,
        "completion_record": completions,
        "credential": credentials,
        "verification_request": verification_requests,
        "revocation": revocations,
        "audit_event": audit_events,
        "anomaly_fixtures": anomaly_fixtures,
        "ground_truth": ground_truth,
    }

def write_exports(data, outdir: Path, include_sql=True):
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = []
    for table, rows in data.items():
        if table == "ground_truth":
            filename = "ground_truth"
        else:
            filename = table
        if not rows:
            # Still emit a CSV with no header only for truly empty tables; schema manifest documents it.
            rows = []
        json_path = outdir / f"{filename}.json"
        json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if rows:
            fields = list(dict.fromkeys(key for row in rows for key in row.keys()))
            with (outdir / f"{filename}.csv").open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        else:
            (outdir / f"{filename}.csv").write_text("", encoding="utf-8")
        manifest.append({"file": f"{filename}.csv", "rows": len(rows),
                         "sha256_csv": hashlib.sha256((outdir/f"{filename}.csv").read_bytes()).hexdigest(),
                         "sha256_json": hashlib.sha256((outdir/f"{filename}.json").read_bytes()).hexdigest()})
    if include_sql:
        sql_lines = ["PRAGMA foreign_keys=ON;", "BEGIN;"]
        # SQLite-ready generic inserts. Create tables via schema.sql separately.
        for table, rows in data.items():
            if table in {"ground_truth", "anomaly_fixtures"} or not rows:
                continue
            cols = list(rows[0].keys())
            for row in rows:
                values = []
                for col in cols:
                    v = row[col]
                    if v is None or v == "":
                        values.append("NULL")
                    elif isinstance(v, (int, float)):
                        values.append(str(v))
                    else:
                        values.append("'" + str(v).replace("'", "''") + "'")
                sql_lines.append(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(values)});")
        sql_lines.append("COMMIT;")
        (outdir / "seed.sql").write_text("\n".join(sql_lines) + "\n", encoding="utf-8")
    (outdir / "source_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    summary = {"tables": {k: len(v) for k,v in data.items()},
               "total_rows": sum(len(v) for v in data.values())}
    (outdir / "generation_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic credential data.")
    parser.add_argument("--out", default="data/generated")
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    parser.add_argument("--learners", type=int, default=20000)
    parser.add_argument("--courses", type=int, default=1000)
    parser.add_argument("--credentials", type=int, default=10000)
    parser.add_argument("--verifications", type=int, default=5000)
    args = parser.parse_args()
    data = make_rows(args.seed, args.learners, args.courses, args.credentials, args.verifications)
    write_exports(data, Path(args.out))
    summary_path = Path(args.out) / "generation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["seed"] = args.seed
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(Path(args.out)), "seed": args.seed,
                      "rows": {k: len(v) for k,v in data.items()}}, indent=2))

if __name__ == "__main__":
    main()
