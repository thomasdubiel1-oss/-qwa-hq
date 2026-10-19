import unittest
from .idempotency import IdempotencyStore
from .request_context import Metrics, RequestContext
class ExecutionSafetyTests(unittest.TestCase):
    def test_request_context_is_unique(self):
        a=RequestContext.create("hermes"); b=RequestContext.create("hermes")
        self.assertNotEqual(a.request_id,b.request_id); self.assertNotEqual(a.trace_id,b.trace_id)
    def test_idempotency(self):
        s=IdempotencyStore(); s.put("r1",{"status":"executed"}); self.assertEqual(s.get("r1"),{"status":"executed"})
    def test_metrics(self):
        m=Metrics(); m.increment("tool.calls"); m.increment("tool.calls"); self.assertEqual(m.counters["tool.calls"],2)
