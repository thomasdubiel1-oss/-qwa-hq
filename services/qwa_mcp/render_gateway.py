"""Provider-neutral Render HTTP gateway with deploy polling and paginated logs."""
import json
import os
import time
from urllib import error, parse, request

TERMINAL_SUCCESS={"live"}
TERMINAL_FAILURE={"build_failed","update_failed","canceled","deactivated","pre_deploy_failed"}

class RenderGateway:
    def __init__(self,api_key=None,base_url="https://api.render.com/v1"):
        self.api_key=api_key or os.environ.get("RENDER_API_KEY")
        self.base_url=base_url.rstrip("/")
        if not self.api_key: raise ValueError("RENDER_API_KEY is required")
    def _request(self,method,path,payload=None):
        body=None if payload is None else json.dumps(payload).encode()
        req=request.Request(self.base_url+path,data=body,method=method,
            headers={"Accept":"application/json","Content-Type":"application/json","Authorization":"Bearer "+self.api_key})
        try:
            with request.urlopen(req,timeout=30) as response:
                raw=response.read().decode()
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raise RuntimeError(f"Render API {exc.code}: {exc.read().decode(errors='replace')}") from exc
    def deploy(self,service,revision):
        return self._request("POST",f"/services/{parse.quote(service,safe='')}/deploys",{"commitId":revision})
    def status(self,service):
        data=self._request("GET",f"/services/{parse.quote(service,safe='')}/deploys?limit=1")
        items=data.get("deploys",data if isinstance(data,list) else [])
        return items[0] if items else data
    def deployment_status(self,service,deploy_id):
        return self._request("GET",f"/services/{parse.quote(service,safe='')}/deploys/{parse.quote(deploy_id,safe='')}")
    def logs(self,owner_id,resource,start_time=None,end_time=None):
        params={"ownerId":owner_id,"resource":resource}
        if start_time: params["startTime"]=start_time
        if end_time: params["endTime"]=end_time
        return self._request("GET","/logs?"+parse.urlencode(params,doseq=True))
    def wait_for_deploy(self,service,deploy_id,timeout_seconds=900,poll_seconds=5):
        deadline=time.monotonic()+timeout_seconds
        while time.monotonic()<deadline:
            result=self.deployment_status(service,deploy_id)
            status=result.get("status")
            if status in TERMINAL_SUCCESS: return result
            if status in TERMINAL_FAILURE: raise RuntimeError(f"Render deployment {deploy_id} failed with status {status}")
            time.sleep(poll_seconds)
        raise TimeoutError(f"Render deployment {deploy_id} did not finish within {timeout_seconds}s")
