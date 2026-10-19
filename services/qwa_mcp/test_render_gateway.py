import unittest
from unittest.mock import Mock, patch

from .render_gateway import RenderGateway


class RenderGatewayTests(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                RenderGateway()

    def test_deploy_uses_exact_commit(self):
        gateway = RenderGateway(api_key="test")
        gateway._request = Mock(return_value={"id": "dep_1", "status": "created"})
        result = gateway.deploy("srv/1", "0123456789abcdef0123456789abcdef01234567")
        self.assertEqual(result["id"], "dep_1")
        gateway._request.assert_called_once_with(
            "POST", "/services/srv%2F1/deploys",
            {"commitId": "0123456789abcdef0123456789abcdef01234567"},
        )

    def test_wait_returns_live(self):
        gateway = RenderGateway(api_key="test")
        gateway.deployment_status = Mock(return_value={"id": "dep_1", "status": "live"})
        self.assertEqual(
            gateway.wait_for_deploy("srv_1", "dep_1", timeout_seconds=1, poll_seconds=1)["status"],
            "live",
        )

    def test_wait_raises_on_failure(self):
        gateway = RenderGateway(api_key="test")
        gateway.deployment_status = Mock(return_value={"id": "dep_1", "status": "build_failed"})
        with self.assertRaises(RuntimeError):
            gateway.wait_for_deploy("srv_1", "dep_1", timeout_seconds=1, poll_seconds=1)

    def test_logs_include_owner_and_resource(self):
        gateway = RenderGateway(api_key="test")
        gateway._request = Mock(return_value={"logs": []})
        gateway.logs("owner_1", "srv_1", "2026-10-19T00:00:00Z", "2026-10-19T01:00:00Z")
        path = gateway._request.call_args.args[1]
        self.assertIn("ownerId=owner_1", path)
        self.assertIn("resource=srv_1", path)


if __name__ == "__main__":
    unittest.main()
