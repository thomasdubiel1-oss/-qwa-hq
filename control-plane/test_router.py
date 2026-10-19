import unittest
from router import Request, authorize

class RouterTests(unittest.TestCase):
    def test_read_is_allowed(self):
        self.assertEqual(authorize(Request('agent','read','read','repo')).decision,'allow')
    def test_dev_write_is_allowed(self):
        self.assertEqual(authorize(Request('engineer','development','write','branch')).decision,'allow')
    def test_prod_requires_approval(self):
        self.assertEqual(authorize(Request('operator','production','deploy','prod',True)).decision,'approval_required')
    def test_nonprod_cannot_access_prod(self):
        self.assertEqual(authorize(Request('engineer','staging','deploy','prod',True)).decision,'deny')

if __name__ == '__main__':
    unittest.main()
