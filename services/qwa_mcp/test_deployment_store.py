import tempfile
import unittest

from .deployment_store import DeploymentRecord, SQLiteDeploymentStore


class DeploymentStoreTests(unittest.TestCase):
    def _record(self, deploy_id="dep_1", revision=None):
        return DeploymentRecord(
            "req_1", "trace_1", "qwa-api", "render", "srv_1",
            revision or "a" * 40, deploy_id, "created",
        )

    def test_persists_and_replays_by_request_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            record = self._record()
            first = store.create(record)
            second = store.create(record)
            self.assertEqual(first, second)
            self.assertEqual(store.get("req_1").deploy_id, "dep_1")

    def test_replay_with_changed_identity_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            store.create(self._record())
            with self.assertRaises(ValueError):
                store.create(self._record(revision="b" * 40))

    def test_get_and_update_by_deploy_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            store.create(self._record())
            self.assertEqual(store.get_by_deploy_id("dep_1").request_id, "req_1")
            self.assertEqual(store.update_status_by_deploy_id("dep_1", "live").status, "live")

    def test_updates_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            store.create(self._record())
            self.assertEqual(store.update_status("req_1", "live").status, "live")

    def test_missing_update_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteDeploymentStore(f"{tmp}/deployments.sqlite3")
            with self.assertRaises(KeyError):
                store.update_status("missing", "live")


if __name__ == "__main__":
    unittest.main()
