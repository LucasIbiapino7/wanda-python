from fastapi import APIRouter, Depends
from wanda_python.services.validate_service import ValidateService
from wanda_python.services.round_service import RoundService
from wanda_python.schema.validate_dto import ValidateRequest, ValidateResponse
from wanda_python.schema.round_dto import RoundRequestDTO, RoundResponseDTO

router = APIRouter()

# Função que faz a injeção da dependência do validateService
def get_validate_service() -> ValidateService:
    return ValidateService()

# Função que faz a injeção da dependência do roundService
def get_round_service() -> RoundService:
    return RoundService()

@router.post("/feedback", response_model=ValidateResponse)
async def validate(data: ValidateRequest, service: ValidateService = Depends(get_validate_service)):
    # Chama o método do serviço
    return await service.feedback(data)

@router.post("/validate", response_model=ValidateResponse)
async def validate(data: ValidateRequest, service: ValidateService = Depends(get_validate_service)):
    # Chama o método do serviço
    return await service.validate(data)

@router.post("/round", response_model=RoundResponseDTO)
async def round(data: RoundRequestDTO, service: RoundService = Depends(get_round_service)):
    return await service.round_choices(data)