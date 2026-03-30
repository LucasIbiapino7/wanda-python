from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from wanda_python.controllers import validate_controller, session_controller
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from wanda_python.otel import configure_otel
from wanda_python.logging_config import setup_logging
setup_logging()   

configure_otel()

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

# Registrar as rotas
app.include_router(validate_controller.router, prefix="/api", tags=["Validation"])
app.include_router(session_controller.router, prefix="/api", tags=["Session"])

