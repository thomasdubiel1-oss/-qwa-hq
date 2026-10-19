import unittest
from .service_registry import ServiceBinding, ServiceRegistry

class ServiceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ServiceRegistry([ServiceBinding("qwa-api-staging","render","srv_123")])

    def test_resolves_allowlisted_service(self):
        self.assertEqual(self.registry.resolve("qwa-api-staging").resource_id, "srv_123")

    def test_unknown_service_fails_closed(self):
        with self.assertRaises(KeyError):
            self.registry.resolve("production")

    def test_non_staging_binding_is_rejected(self):
        registry = ServiceRegistry([ServiceBinding("qwa-api","render","srv_prod","production")])
        with self.assertRaises(PermissionError):
            registry.resolve("qwa-api")

if __name__ == "__main__":
    unittest.main()
