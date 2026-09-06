from mcp.server.fastmcp import FastMCP
from tools import *
mcp=FastMCP("devops-mcp-server")
for fn in [k8s_get_pods,k8s_get_events,k8s_get_logs,get_pipeline,get_test_results,compare_releases,query_metrics,find_similar_incident,send_notification,restart_pod,scale_deployment,rollback_deployment]:
    mcp.tool()(fn)
if __name__ == "__main__": mcp.run()
