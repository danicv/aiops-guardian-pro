import asyncio
import os
from itertools import count
from pathlib import Path
from threading import Lock
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

app = FastAPI(title="Northstar Supply Demo Store", version="1.0.0")
VERSION = os.getenv('VERSION', 'v1.9.0')
SCOPE = (os.getenv('SERVICE_NAME', 'checkout-api'), os.getenv('ENVIRONMENT', 'prod'), os.getenv('NAMESPACE', 'default'))
LABELS = ('service', 'environment', 'namespace', 'route', 'method', 'status')
REQUESTS = Counter('http_server_requests_total', 'Completed HTTP requests', LABELS)
DURATION = Histogram('http_server_duration_seconds', 'HTTP request duration in seconds', LABELS,
                     buckets=(.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10))
ORDER_ATTEMPTS = Counter('checkout_orders_total', 'Mock checkout attempts by outcome',
                         ('service', 'environment', 'namespace', 'outcome'))
ORDER_VALUE = Counter('checkout_revenue_usd_total', 'Synthetic confirmed order value in USD',
                      ('service', 'environment', 'namespace'))

PRODUCTS = [
    {"sku": "FIELD-JOURNAL", "name": "Field Notes Journal", "category": "Paper goods", "price_cents": 1800,
     "description": "A sturdy, lay-flat notebook for plans, lists, and little ideas.",
     "image": "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=900&q=85"},
    {"sku": "TRAIL-BOTTLE", "name": "Trail Bottle", "category": "Everyday carry", "price_cents": 3200,
     "description": "Double-wall stainless steel, made for the commute and the long way home.",
     "image": "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=900&q=85"},
    {"sku": "CANVAS-TOTE", "name": "Market Canvas Tote", "category": "Carry goods", "price_cents": 2600,
     "description": "A roomy recycled-cotton carryall with an easy-access inside pocket.",
     "image": "https://images.unsplash.com/photo-1590874103328-eac38a683ce7?auto=format&fit=crop&w=900&q=85"},
    {"sku": "DESK-TRAY", "name": "Oak Desk Tray", "category": "Workspace", "price_cents": 4400,
     "description": "A simple landing place for keys, cards, and the small things you use daily.",
     "image": "https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?auto=format&fit=crop&w=900&q=85"},
]
PRODUCT_BY_SKU = {product['sku']: product for product in PRODUCTS}
ORDERS = []
ORDER_IDS = count(1)
ORDER_LOCK = Lock()
PAGE = Path(__file__).parent / 'static' / 'index.html'


class CartLine(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(ge=1, le=10)


class OrderRequest(BaseModel):
    items: list[CartLine] = Field(min_length=1, max_length=20)


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


@app.get('/', include_in_schema=False)
def storefront():
    return FileResponse(PAGE)


@app.get('/metrics', include_in_schema=False)
def metrics():
    return Response(generate_latest(), headers={'Content-Type': CONTENT_TYPE_LATEST})


@app.get('/health')
def health():
    return {'status': 'ok', 'version': VERSION}


@app.get('/api/products')
def products():
    return {'products': PRODUCTS, 'currency': 'USD', 'demo_only': True}


@app.get('/api/orders')
def recent_orders():
    with ORDER_LOCK:
        return {'orders': list(reversed(ORDERS[-10:])), 'demo_only': True}


@app.post('/api/orders')
async def create_order(request: OrderRequest, delay_ms: int = Query(default=0, ge=0, le=1000),
                       fail: bool = False):
    if (delay_ms or fail) and os.getenv('ENABLE_DEMO_FAULTS', 'false').lower() != 'true':
        raise HTTPException(403, 'Demo fault controls are disabled')
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    if fail:
        ORDER_ATTEMPTS.labels(*SCOPE, 'unavailable').inc()
        raise HTTPException(503, 'Synthetic checkout service unavailable. No order was placed.')

    lines = []
    for item in request.items:
        product = PRODUCT_BY_SKU.get(item.sku)
        if product is None:
            raise HTTPException(422, f'Unknown product SKU: {item.sku}')
        lines.append({**product, 'quantity': item.quantity,
                      'line_total_cents': product['price_cents'] * item.quantity})
    total_cents = sum(item['line_total_cents'] for item in lines)
    with ORDER_LOCK:
        order_id = f"DEMO-{next(ORDER_IDS):05d}"
        order = {'order_id': order_id, 'status': 'confirmed', 'items': lines,
                 'total_cents': total_cents, 'currency': 'USD', 'version': VERSION}
        ORDERS.append(order)
        del ORDERS[:-50]
    ORDER_ATTEMPTS.labels(*SCOPE, 'confirmed').inc()
    ORDER_VALUE.labels(*SCOPE).inc(total_cents / 100)
    return {**order, 'demo_only': True, 'payment_processed': False}


@app.get('/checkout')
async def checkout(delay_ms: int = Query(default=0, ge=0, le=1000), fail: bool = False):
    # Retain the small health-check endpoint used by older demo scripts.
    if (delay_ms or fail) and os.getenv('ENABLE_DEMO_FAULTS', 'false').lower() != 'true':
        raise HTTPException(403, 'Demo fault controls are disabled')
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    if fail:
        raise HTTPException(503, 'Intentional local demonstration failure')
    return {'status': 'accepted', 'version': VERSION, 'demo_only': True}

