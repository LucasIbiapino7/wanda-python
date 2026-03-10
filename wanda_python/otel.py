import os
import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
# Logs
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter


def configure_otel():
    set_global_textmap(TraceContextTextMapPropagator())

    resource = Resource.create({
        "service.name": os.getenv("OTEL_SERVICE_NAME", "wanda-python")
    })

    _configure_traces(resource)
    _configure_logs(resource)
    configure_logging()


def _configure_traces(resource):
    provider = TracerProvider(resource=resource, sampler=ALWAYS_ON)
    exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_ENDPOINT", "http://localhost:4317"),
        insecure=True
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def _configure_logs(resource):
    logger_provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(
        endpoint=os.getenv("OTEL_ENDPOINT", "http://localhost:4317"),
        insecure=True
    )
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    set_logger_provider(logger_provider)
    # Anexa ao logging padrão do Python
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        record.trace_id = format(ctx.trace_id, '032x') if ctx.is_valid else ''
        record.span_id = format(ctx.span_id, '016x') if ctx.is_valid else ''
        return True


def configure_logging():
    handler = logging.StreamHandler()
    handler.addFilter(TraceIdFilter())
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(trace_id)s,%(span_id)s] %(levelname)s %(name)s - %(message)s'
    ))
    logging.basicConfig(level=logging.INFO, handlers=[handler])