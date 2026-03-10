import logging
import os
from pythonjsonlogger import jsonlogger
from opentelemetry import trace

SERVICE_NAME = os.getenv('SERVICE_NAME', 'wanda-python')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'text')  
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

class OtelJsonFormatter(jsonlogger.JsonFormatter):
    """Injeta trace_id e span_id automaticamente em todo log."""
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        span = trace.get_current_span()
        ctx  = span.get_span_context() if span else None
        log_record['service']  = SERVICE_NAME
        log_record['trace_id'] = format(ctx.trace_id, '032x') if ctx and ctx.is_valid else ''
        log_record['span_id']  = format(ctx.span_id, '016x')  if ctx and ctx.is_valid else ''

def setup_logging():
    handler = logging.StreamHandler()
    if LOG_FORMAT == 'json':
        fmt = OtelJsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
    else:
        fmt = logging.Formatter(
            '%(asctime)s [%(trace_id)s,%(span_id)s] %(levelname)-5s %(name)s - %(message)s',
            defaults={'trace_id': '', 'span_id': ''}
        )
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)
