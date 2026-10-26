import tempfile
import unittest
from pathlib import Path
from datetime import date, datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src import database, services
from src.main import app


class CredentialAPITests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "api_test.db"

        self.patcher = patch(
            "src.services.connect",
            side_effect=lambda: database.connect(self.db),
        )
        self.patcher.start()

        database.initialize_database(self.db)

        today = date.today().isoformat()

        services.create_learner(
            "API-LRN-001",
            "Test Learner",
            "api-learner@example.test",
        )
        services.create_course(
            "API-CRS-001",
            "API Testing",
            today,
        )
        services.create_issuer(
            "API-ISS-001",
            "Test Issuer",
            today,
        )
        services.create_rule(
            "API-RUL-001",
            "API-CRS-001",
            70,
            80,
            today,
        )
        services.create_completion(
            "API-CMP-001",
            "API-LRN-001",
            "API-CRS-001",
            90,
            95,
            "COMPLETED",
            datetime.now(timezone.utc).isoformat(),
        )

        self.startup_patcher = patch("src.main.initialize_database")
        self.startup_patcher.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.startup_patcher.stop()
        self.patcher.stop()
        self.tmp.cleanup()

    def test_issue_and_verify_through_api(self):
        response = self.client.post(
            "/credentials/issue",
            json={
                "learner_id": "API-LRN-001",
                "course_id": "API-CRS-001",
                "issuer_id": "API-ISS-001",
            },
        )

        self.assertEqual(response.status_code, 200)
        credential_id = response.json()["credential_id"]

        verification = self.client.get(
            f"/credentials/{credential_id}/verify"
        )

        self.assertEqual(verification.status_code, 200)
        self.assertEqual(verification.json()["result"], "VALID")

    def test_revoked_credential_returns_revoked_through_api(self):
        issued = services.issue_credential(
            "API-LRN-001",
            "API-CRS-001",
            "API-ISS-001",
        )
        credential_id = issued["credential_id"]

        response = self.client.post(
            f"/credentials/{credential_id}/revoke",
            json={"reason": "API integration test"},
        )

        self.assertEqual(response.status_code, 200)

        verification = self.client.get(
            f"/credentials/{credential_id}/verify"
        )

        self.assertEqual(verification.status_code, 200)
        self.assertEqual(verification.json()["result"], "REVOKED")

    def test_tampered_credential_returns_tampered_through_api(self):
        issued = services.issue_credential(
            "API-LRN-001",
            "API-CRS-001",
            "API-ISS-001",
        )
        credential_id = issued["credential_id"]

        with database.connect(self.db) as conn:
            conn.execute(
                """
                UPDATE credential
                SET payload_json = ?
                WHERE credential_id = ?
                """,
                ('{"credential_id":"ALTERED"}', credential_id),
            )

        response = self.client.get(
            f"/credentials/{credential_id}/verify"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["result"], "TAMPERED")


        # The fixture must be rejected or flagged by a validation rule.
        # The current issue API does not accept an issued_at parameter,
        # so this test verifies the anomaly's chronological condition only.


if __name__ == "__main__":
    unittest.main()
