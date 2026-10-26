import csv
import hashlib
import json
import argparse
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate the expected characteristics of generated anomaly fixtures."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/generated-final"),
        help="Directory containing anomaly_fixtures.json and credential.csv "
             "(default: data/generated-final)",
    )
    return parser.parse_args()


DATA = parse_args().data_dir

def load_json(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def load_csv(name):
    with (DATA / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

fixtures = load_json("anomaly_fixtures.json")
credentials = load_csv("credential.csv")
by_id = {r["credential_id"]: r for r in credentials}
results = []

def record(anomaly, passed, detail):
    results.append((anomaly, passed, detail))
    print(f"[{'PASS' if passed else 'FAIL'}] {anomaly}: {detail}")

for f in fixtures:
    kind = f["issue_type"]
    cid = f["credential_id"]

    if kind == "ISSUED_BEFORE_COMPLETION":
        passed = f["issued_at"] < f["completed_at"]
        record(kind, passed, "Issue time precedes completion time")

    elif kind == "DUPLICATE_CREDENTIAL_ID":
        passed = cid in by_id and f.get("attempt") == "INSERT_DUPLICATE_ID"
        record(kind, passed, "Duplicate attempt targets an existing baseline ID")

    elif kind == "REVOKED_VERIFIES_ACTIVE":
        credential = by_id.get(cid)
        passed = (
            credential is not None
            and credential["status"] == "REVOKED"
            and f.get("injected_verification_result") == "ACTIVE"
            and f.get("expected_detection") == "MUST_RETURN_REVOKED"
        )
        record(kind, passed, "Fixture demonstrates ACTIVE is incorrect for a revoked credential")

    elif kind == "ALTERED_HASH_NOT_DETECTED":
        actual_hash = hashlib.sha256(
            f["tampered_payload_json"].encode("utf-8")
        ).hexdigest()
        passed = actual_hash != f["stored_payload_hash"]
        record(kind, passed, "Tampered payload hash differs from stored hash")

    else:
        record(kind, False, "Unknown anomaly type")

print(f"\nPassed: {sum(p for _, p, _ in results)}/{len(results)}")
if not results or not all(p for _, p, _ in results):
    raise SystemExit(1)
