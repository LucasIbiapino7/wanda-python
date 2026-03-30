from fastapi import APIRouter, Depends
from wanda_python.services.round_service import RoundService
from wanda_python.schema.session_dto import (SessionCreateRequestDTO, SessionCreateResponseDTO,
    SessionExecuteRequestDTO,SessionExecuteResponseDTO)

router = APIRouter()

def get_round_service() -> RoundService:
    return RoundService()


@router.post("/session", response_model=SessionCreateResponseDTO)
async def create_session(data: SessionCreateRequestDTO, service: RoundService = Depends(get_round_service)):
    session_id = await service.create_session(data.player1Function, data.player2Function)
    return SessionCreateResponseDTO.create(session_id)


@router.post("/session/execute", response_model=SessionExecuteResponseDTO)
async def execute_round(data: SessionExecuteRequestDTO, service: RoundService = Depends(get_round_service)):
    result = await service.execute_round(data.sessionId, data.player1Parameters, data.player2Parameters)
    return SessionExecuteResponseDTO.create(result)


@router.delete("/session/{session_id}", status_code=200)
async def close_session(session_id: str, service: RoundService = Depends(get_round_service)):
    await service.close_session(session_id)
    return {"message": "Sessão encerrada."}