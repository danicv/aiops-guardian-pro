def k8s_get_pods(namespace="default", app="checkout-api"):
    return {"namespace":namespace,"app":app,"pods":[{"name":"checkout-api-a","status":"CrashLoopBackOff","restarts":4},{"name":"checkout-api-b","status":"CrashLoopBackOff","restarts":3},{"name":"checkout-api-c","status":"CrashLoopBackOff","restarts":2}]}
def k8s_get_events(namespace="default", app="checkout-api"):
    return {"events":[{"reason":"OOMKilled","message":"Container exceeded memory limit."}]}
def k8s_get_logs(namespace="default", app="checkout-api", tail=100):
    return {"logs":["worker terminated","memory allocation failed"],"tail":tail}
def get_pipeline(pipeline_id="PIPE-1847"):
    return {"id":pipeline_id,"status":"success","stage":"deploy-prod","version":"v2.0.0"}
def get_test_results(pipeline_id="PIPE-1847"):
    return {"pipeline_id":pipeline_id,"unit":"passed","load_test":"missing"}
def compare_releases(current="v2.0.0", previous="v1.9.0"):
    return {"current":current,"previous":previous,"changes":{"memory":{"before":"1Gi","after":"128Mi"}}}
def query_metrics(query):
    return {"query":query,"series":[{"timestamp":"demo","value":6.8}]}
def find_similar_incident(application="checkout-api"):
    return {"application":application,"incident_id":"INC-1024","resolution":"rollback resource-limit change"}
def send_notification(channel,destination,message):
    return {"channel":channel,"destination":destination,"status":"accepted","message":message}
def restart_pod(namespace,pod):
    return {"action":"restart_pod","namespace":namespace,"pod":pod,"status":"demo-executed"}
def scale_deployment(namespace,deployment,replicas):
    return {"action":"scale_deployment","namespace":namespace,"deployment":deployment,"replicas":replicas,"status":"demo-executed"}
def rollback_deployment(namespace,deployment,target_version):
    return {"action":"rollback_deployment","namespace":namespace,"deployment":deployment,"target_version":target_version,"status":"demo-executed"}
