import tempfile
import unittest
from pathlib import Path

from .github_adapter import GitHubConnectorAdapter
from .knowledge_adapter import ScopedKnowledgeAdapter


class FakeGateway:
    def inspect_repo(self, repo): return {"repo": repo, "ok": True}
    def create_branch(self, repo, branch, base): return {"branch": branch, "base": base}
    def create_pr(self, repo, head, base, title): return {"head": head, "base": base, "title": title}
    def ci_status(self, repo, sha): return {"sha": sha, "state": "success"}


class ProviderAdapterTests(unittest.TestCase):
    def test_github_gateway_is_normalized(self):
        result = GitHubConnectorAdapter(FakeGateway()).create_branch("org/repo", "feature/x", "main")
        self.assertTrue(result.ok)
        self.assertEqual(result.data["branch"], "feature/x")

    def test_knowledge_scope_blocks_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PermissionError):
                ScopedKnowledgeAdapter(Path(tmp)).read("private/secret.md")

    def test_knowledge_scope_blocks_parent_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                ScopedKnowledgeAdapter(Path(tmp)).read("../secret.md")

    def test_knowledge_write_stays_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            adapter = ScopedKnowledgeAdapter(Path(tmp))
            result = adapter.write_decision("decisions/test.md", "# Decision")
            self.assertTrue(result.ok)
            self.assertTrue((Path(tmp) / "decisions/test.md").exists())


if __name__ == "__main__":
    unittest.main()
