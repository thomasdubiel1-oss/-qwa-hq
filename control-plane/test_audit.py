import tempfile
import unittest
from pathlib import Path
from audit import record
class AuditTests(unittest.TestCase):
    def test_event(self):
        with tempfile.TemporaryDirectory() as d:
            p=str(Path(d)/"audit.jsonl"); record(p,actor="test",action="read",resource="repo",decision="allow",request_id="r1")
            self.assertIn('"request_id":"r1"',Path(p).read_text())
if __name__=='__main__': unittest.main()
