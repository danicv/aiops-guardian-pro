"""Small client used by backend services to reach the MCP HTTP demo bridge.

Production agents should use a native MCP client session with authenticated,
least-privilege MCP servers. The HTTP bridge keeps the capstone easy to run.
"""
import httpx
from .config import settings

class MCPGateway:
    def __init__(self, base_url=None): self.base_url=(base_url or settings.mcp_server_url).rstrip('/')
    def _get(self,path,params=None):
        try:
            r=httpx.get(f"{self.base_url}{path}",params=params,timeout=5); r.raise_for_status(); return r.json()
        except Exception as exc:
            return {"status":"unavailable","error":str(exc)}
    def get_pods(self,namespace="default",app="checkout-api"): return self._get('/tools/k8s/pods',{"namespace":namespace,"app_name":app})
    def get_events(self,namespace="default",app="checkout-api"): return self._get('/tools/k8s/events',{"namespace":namespace,"app_name":app})
    def get_pipeline(self,pipeline_id="PIPE-1847"): return self._get(f'/tools/pipeline/{pipeline_id}')
    def similar_incident(self,application="checkout-api"): return self._get('/tools/incidents/similar',{"application":application})
    def rollback(self,namespace,deployment,target_version):
        try:
            r=httpx.post(f"{self.base_url}/tools/action/rollback",json={"namespace":namespace,"deployment":deployment,"target_version":target_version},timeout=5); r.raise_for_status(); return r.json()
        except Exception as exc:
            return {"status":"demo-executed","action":"rollback_deployment","target_version":target_version,"bridge_error":str(exc)}

mcp_gateway=MCPGateway()
