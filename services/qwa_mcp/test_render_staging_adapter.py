import unittest
from unittest.mock import Mock

from .render_staging_adapter import RenderStagingAdapter
from .service_registry import ServiceBinding, ServiceRegistry


class RenderStagingAdapterTests(unittest.TestCase):
    def setUp(self):
        self.gateway = Mock()
        self.gateway.deploy.return_value = {"id": "dep_123", "status": "created"}
        self.gateway.deployment_status.return_value = {"id": "dep_123", "status": "live"}
        self.gateway.logs.return_value = {"logs": []}
        self.gateway.wait_for_deploy.return_value = {"id": "dep_123", "status": "live"}
        self.registry = ServiceRegistry([
            ServiceBinding("qwa-api", "render", "srv_123", "staging", "owner_123"),
        ])
        self.adapter = RenderStagingAdapter(self.registry, self.gateway)

    def test_deploy_uses_bound_resource_and_commit_sha(self):
        result = self.adapter.deploy(
            "qwa-api", "0123456789abcdef0123456789abcdef01234567",
            request_id="req_1", trace_id="trace_1",
        )
        self.assertTrue(result.ok)
        self.gateway.deploy.assert_called_once_with(
            "srv_123", "0123456789abcdef0123456789abcdef01234567"
        )
        self.assertEqual(result.data["deploy_id"], "dep_123")
        self.assertEqual(result.data["request_id"], "req_1")

    def test_unknown_service_fails_closed(self):
        result = self.adapter.deploy("unknown", "0123456789abcdef0123456789abcdef01234567")
        self.assertFalse(result.ok)
        self.assertIn("unknown service", result.error)

    def test_non_render_binding_is_rejected(self):
        registry = ServiceRegistry([ServiceBinding("other", "fly", "app_1")])
        result = RenderStagingAdapter(registry, self.gateway).deploy(
            "other", "0123456789abcdef0123456789abcdef01234567"
        )
        self.assertFalse(result.ok)
        self.assertIn("Render", result.error)

    def test_invalid_revision_is_rejected(self):
        result = self.adapter.deploy("qwa-api", "main")
        self.assertFalse(result.ok)
        self.assertIn("40-character", result.error)

    def test_logs_require_owner_binding(self):
        registry = ServiceRegistry([ServiceBinding("qwa-api", "render", "srv_123")])
        result = RenderStagingAdapter(registry, self.gateway).logs("qwa-api")
        self.assertFalse(result.ok)
        self.assertIn("owner_id", result.error)

    def test_wait_for_deploy_uses_bound_resource(self):
        result = self.adapter.wait("qwa-api", "dep_123", timeout_seconds=10, poll_seconds=1)
        self.assertTrue(result.ok)
        self.gateway.wait_for_deploy.assert_called_once_with("srv_123", "dep_123", 10, 1)


if __name__ == "__main__":
    unittest.main()
