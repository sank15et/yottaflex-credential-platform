
import tempfile
import unittest
from pathlib import Path
from datetime import date, datetime, timezone
from unittest.mock import patch

from src import database, services


class ServiceTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"

        self.patcher = patch(
            "src.services.connect",
            side_effect=lambda: database.connect(self.db),
        )
        self.patcher.start()

        database.initialize_database(self.db)

        today = date.today().isoformat()
        completed_at = datetime.now(timezone.utc).isoformat()

        services.create_learner(
            "LRN-000001",
            "Asha Patil",
            "asha@example.test",
        )

        services.create_course(
            "CRS-000001",
            "Python Basics",
            today,
        )

        services.create_issuer(
            "ISS-000001",
            "Demo Issuer",
            today,
        )

        services.create_rule(
            "RUL-000001",
            "CRS-000001",
            70,
            80,
            today,
        )

        services.create_completion(
            "CMP-LRN-000001-CRS-000001",
            "LRN-000001",
            "CRS-000001",
            90,
            95,
            "COMPLETED",
            completed_at,
        )

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_issue_successfully(self):
        result = services.issue_credential(
            "LRN-000001",
            "CRS-000001",
            "ISS-000001",
        )

        self.assertEqual(result["status"], "ACTIVE")
        self.assertTrue(result["credential_id"].startswith("CRD-"))

    def test_reject_incomplete_or_missing_completion(self):
        with database.connect(self.db) as conn:
            conn.execute(
                """
                UPDATE completion_record
                SET completion_status = 'IN_PROGRESS'
                WHERE completion_id = ?
                """,
                ("CMP-LRN-000001-CRS-000001",),
            )

        with self.assertRaisesRegex(
            ValueError,
            "completion requirements",
        ):
            services.issue_credential(
                "LRN-000001",
                "CRS-000001",
                "ISS-000001",
            )

    def test_duplicate_issue_rejected(self):
        services.issue_credential(
            "LRN-000001",
            "CRS-000001",
            "ISS-000001",
        )

        with self.assertRaisesRegex(ValueError, "already issued"):
            services.issue_credential(
                "LRN-000001",
                "CRS-000001",
                "ISS-000001",
            )

    def test_revoke_then_verify(self):
        result = services.issue_credential(
            "LRN-000001",
            "CRS-000001",
            "ISS-000001",
        )

        services.revoke_credential(
            result["credential_id"],
            "Test revocation",
        )

        verification = services.verify_credential(
            result["credential_id"]
        )

        self.assertEqual(verification["result"], "REVOKED")

    def test_missing_credential_verification(self):
        result = services.verify_credential("CRD-2099-999999")

        self.assertEqual(result["result"], "NOT_FOUND")

    def test_reject_future_completion(self):
        future = "2999-01-01T00:00:00+00:00"

        with database.connect(self.db) as conn:
            conn.execute(
                """
                UPDATE completion_record
                SET completed_at = ?
                WHERE completion_id = ?
                """,
                (
                    future,
                    "CMP-LRN-000001-CRS-000001",
                ),
            )

        with self.assertRaisesRegex(ValueError, "future"):
            services.issue_credential(
                "LRN-000001",
                "CRS-000001",
                "ISS-000001",
            )

    def test_tampered_payload_is_detected(self):
        result = services.issue_credential(
            "LRN-000001",
            "CRS-000001",
            "ISS-000001",
        )

        credential_id = result["credential_id"]

        with database.connect(self.db) as conn:
            conn.execute(
                """
                UPDATE credential
                SET payload_json = ?
                WHERE credential_id = ?
                """,
                ('{"credential_id":"TAMPERED"}', credential_id),
            )

        verification = services.verify_credential(credential_id)

        self.assertEqual(verification["result"], "TAMPERED")

    def test_revoked_credential_never_verifies_as_active(self):
        result = services.issue_credential(
            "LRN-000001",
            "CRS-000001",
            "ISS-000001",
        )

        credential_id = result["credential_id"]

        services.revoke_credential(
            credential_id,
            "Test revocation",
        )

        verification = services.verify_credential(credential_id)

        self.assertEqual(verification["result"], "REVOKED")
        self.assertNotEqual(verification["result"], "VALID")

    def test_credential_id_collision_uses_next_available_id(self):
        # Create a second learner and completion for a seeded credential.
        services.create_learner(
            "LRN-000002",
            "Rohan Shah",
            "rohan@example.test",
        )

        services.create_completion(
            "CMP-LRN-000002-CRS-000001",
            "LRN-000002",
            "CRS-000001",
            85,
            90,
            "COMPLETED",
            datetime.now(timezone.utc).isoformat(),
        )

        year = datetime.now(timezone.utc).year
        colliding_id = f"CRD-{year}-000002"

        # Seed an existing credential with the ID the next issue would try.
        with database.connect(self.db) as conn:
            payload = services.canonical_json({
                "credential_id": colliding_id,
                "learner_id": "LRN-000002",
                "course_id": "CRS-000001",
                "completion_id": "CMP-LRN-000002-CRS-000001",
                "issuer_id": "ISS-000001",
                "issued_at": datetime.now(timezone.utc).isoformat(),
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
                    colliding_id,
                    "LRN-000002",
                    "CRS-000001",
                    "CMP-LRN-000002-CRS-000001",
                    "ISS-000001",
                    datetime.now(timezone.utc).isoformat(),
                    payload,
                    services.sha256_text(payload),
                    services.canonical_json({
                        "algorithm": "SHA-256",
                        "type": "integrity-hash-only",
                        "is_digital_signature": False,
                    }),
                ),
            )

        # There is one existing credential, so the initial candidate is
        # 000002. The service must skip it and select 000003.
        result = services.issue_credential(
            "LRN-000001",
            "CRS-000001",
            "ISS-000001",
        )

        self.assertEqual(
            result["credential_id"],
            f"CRD-{year}-000003",
        )

        self.assertNotEqual(
            result["credential_id"],
            colliding_id,
        )


if __name__ == "__main__":
    unittest.main()
