"""In-memory idempotency guard; replace with durable storage in production."""
class IdempotencyStore:
    def __init__(self): self.results = {}
    def get(self, request_id): return self.results.get(request_id)
    def put(self, request_id, result): self.results[request_id] = result
