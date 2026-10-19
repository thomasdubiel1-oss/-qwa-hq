"""Provider-neutral Render HTTP gateway."""
import json
import os
from urllib import error, request

class RenderGateway:
    def __init__(self, api_key=None, base_url="https://api.render.com/v1"):
        self.api_key = api_key or os.environ.get("RENDER_API_KEY")
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise ValueError("RENDER_API_KEY is required")

    def _request(self, method, path, payload=None):
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.base_url + path, data=body, method=method,
            headers={"Accept": "application/json", "Content-Type": "application/json",
                     "Authorization": "Bearer " + self.api_key},
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Render API {exc.code}: {detail}") from exc

    def deploy(self, service, revision):
        return self._request("POST", f"/services/{service}/deploys",
                             {"commitId": revision, "deployMode": "build_and_deploy"})

    def status(self, service):
        return self._request("GET", f"/services/{service}/deploys?limit=1")

    def logs(self, service, limit=100):
        bounded = min(max(int(limit), 1), 100)
        return self._request("GET", f"/logs?resource={service}&limit={bounded}")
