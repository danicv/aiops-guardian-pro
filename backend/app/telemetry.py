import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.trace import Status
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

class PrivateSpanExporter(SpanExporter):
    """Export timing and status only; never arbitrary attributes or exception events."""
    def __init__(self, delegate):
        self.delegate = delegate

    def export(self, spans):
        clean = [ReadableSpan(
            name='guardian.operation', context=s.context, parent=s.parent,
            resource=Resource({'service.name': 'aiops-guardian-backend'}),
            kind=s.kind, status=Status(s.status.status_code),
            start_time=s.start_time, end_time=s.end_time,
        ) for s in spans]
        return self.delegate.export(clean)

    def shutdown(self):
        return self.delegate.shutdown()

    def force_flush(self, timeout_millis=30000):
        return self.delegate.force_flush(timeout_millis)

def configure_tracing(service_name):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if endpoint:
        provider.add_span_processor(BatchSpanProcessor(PrivateSpanExporter(OTLPSpanExporter(endpoint=f"{endpoint.rstrip('/')}/v1/traces"))))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

tracer = configure_tracing("aiops-guardian-backend")
