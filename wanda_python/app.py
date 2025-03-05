from fastapi import FastAPI
from wanda_python.controllers import validate_controller

app = FastAPI()

# Registrar as rotas
app.include_router(validate_controller.router, prefix="/api", tags=["Validation"])

