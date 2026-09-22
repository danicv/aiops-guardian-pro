import os
import asyncio
from time import perf_counter
from fastapi import FastAPI, Response, Query, HTTPException
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

app = FastAPI()
VERSION = os.getenv('VERSION', 'v1.9.0')
SCOPE = (os.getenv('SERVICE_NAME', 'checkout-api'), os.getenv('ENVIRONMENT', 'prod'), os.getenv('NAMESPACE', 'default'))
LABELS = ('service', 'environment', 'namespace', 'route', 'method', 'status')
REQUESTS = Counter('http_server_requests_total', 'Completed HTTP requests', LABELS)
DURATION = Histogram('http_server_duration_seconds', 'HTTP request duration in seconds', LABELS,
                     buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10))


@app.middleware('http')
async def record_metrics(request, call_next):
    if request.url.path in ('/metrics', '/health'):
        return await call_next(request)
    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get('route')
        path = getattr(route, 'path', 'unmatched')
        method = request.method if request.method in {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'} else 'OTHER'
        labels = (*SCOPE, path, method, str(status))
        REQUESTS.labels(*labels).inc()
        DURATION.labels(*labels).observe(perf_counter()-started)


@app.get('/metrics', include_in_schema=False)
def metrics():
    return Response(generate_latest(), headers={'Content-Type': CONTENT_TYPE_LATEST})


@app.get('/health')
def health():
    return {'status': 'ok', 'version': VERSION}


@app.get('/checkout')
async def checkout(delay_ms: int = Query(default=0, ge=0, le=1000), fail: bool = False):
    # Fault controls are available only when explicitly enabled on this demo service.
    if (delay_ms or fail) and os.getenv('ENABLE_DEMO_FAULTS', 'false').lower() != 'true':
        raise HTTPException(403, 'Demo fault controls are disabled')
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    if fail:
        raise HTTPException(503, 'Intentional local demonstration failure')
    return {'status': 'accepted', 'version': VERSION}

