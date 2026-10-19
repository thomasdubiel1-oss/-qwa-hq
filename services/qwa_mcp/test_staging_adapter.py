import unittest
from .staging_adapter import StagingAdapter
class FakeStaging:
    def deploy(self,s,r): return {"service":s,"revision":r}
    def status(self,s): return {"service":s,"state":"healthy"}
    def logs(self,s,limit=100): return {"service":s,"limit":limit,"lines":[]}
class StagingTests(unittest.TestCase):
    def test_deploy(self): self.assertTrue(StagingAdapter(FakeStaging()).deploy("qwa-api","abc123").ok)
    def test_log_limit(self): self.assertEqual(StagingAdapter(FakeStaging()).logs("qwa-api",9999).data["limit"],500)
