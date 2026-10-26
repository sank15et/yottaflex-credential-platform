import sqlite3
import sys
from pathlib import Path

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/generated-final/full_validation.db")

if not DB.exists():
    raise SystemExit(f"FAIL: Database not found: {DB}")

con = sqlite3.connect(DB)
try:
    rows = con.execute("""
        SELECT
            c.credential_id,
            c.issued_at,
            cp.completed_at
        FROM credential c
        JOIN completion_record cp
          ON cp.completion_id = c.completion_id
        WHERE cp.completed_at IS NOT NULL
          AND c.issued_at < cp.completed_at
        ORDER BY c.credential_id
    """).fetchall()

    if rows:
        print(f"[FAIL] Found {len(rows)} credentials issued before completion:")
        for credential_id, issued_at, completed_at in rows[:20]:
            print(
                f"  {credential_id}: issued_at={issued_at}, "
                f"completed_at={completed_at}"
            )
        raise SystemExit(1)

    print("[PASS] No credentials issued before completion in database.")
finally:
    con.close()
