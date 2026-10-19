import json
import unittest
from unittest.mock import patch
from .render_gateway import RenderGateway

class RenderGatewayTests(unittest.TestCase):
    def test_requires_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                RenderGateway()

    @patch("services.qwa_mcp.render_gateway.request.urlopen")
    def test_deploy_sends_commit(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps({"id": "dep1", "status": "created"}).encode()
        gateway = RenderGateway("test-key")
        result = gateway.deploy("srv1", "abc123")
        self.assertEqual(result["id"], "dep1")
        sent = urlopen.call_args.args[0]
        self.assertEqual(sent.method, "POST")
        self.assertIn("/services/srv1/deploys", sent.full_url)
        self.assertIn(b'"commitId": "abc123"', sent.data)

    @patch("services.qwa_mcp.render_gateway.request.urlopen")
    def test_status_reads_latest_deploy(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = b'{"deploys":[]}'
        gateway = RenderGateway("test-key")
        self.assertEqual(gateway.status("srv1"), {"deploys": []})

if __name__ == "__main__":
    unittest.main()
