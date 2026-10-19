import tempfile
import unittest

from .deployment_store import DeploymentRecord, SQLiteDeploymentStore


class DeploymentStoreTests(unittest.TestCase):
    def test_persists_and_replays_by_request_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            record = DeploymentRecord(
                "req_1", "trace_1", "qwa-api", "render", "srv_1",
                "a" * 40, "dep_1", "created",
            )
            first = store.create(record)
            second = store.create(record)
            self.assertEqual(first, second)
            self.assertEqual(store.get("req_1").deploy_id, "dep_1")

    def test_updates_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            store.create(DeploymentRecord(
                "req_1", "trace_1", "qwa-api", "render", "srv_1",
                "a" * 40, "dep_1", "created",
            ))
            self.assertEqual(store.update_status("req_1", "live").status, "live")

    def test_missing_update_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            with self.assertRaises(KeyError):
                store.update_status("missing", "live")


if __name__ == "__main__":
    unittest.main()
