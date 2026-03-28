from pydantic import BaseModel, Field
from typing import Any, List, Optional


class SessionCreateRequestDTO(BaseModel):
    player1Function: str = Field(..., description="Código da função do jogador 1")
    player2Function: str = Field(..., description="Código da função do jogador 2")


class SessionCreateResponseDTO(BaseModel):
    sessionId: str = Field(..., description="Identificador da sessão criada")

    @classmethod
    def create(cls, session_id: str):
        return cls(sessionId=session_id)


class SessionExecuteRequestDTO(BaseModel):
    sessionId: str = Field(..., description="Identificador da sessão")
    player1Parameters: List[Any] = Field(..., description="Parâmetros para a função do jogador 1")
    player2Parameters: List[Any] = Field(..., description="Parâmetros para a função do jogador 2")


class SessionExecuteResponseDTO(BaseModel):
    player1Choice: Optional[str] = Field(None, description="Escolha feita pelo jogador 1")
    player2Choice: Optional[str] = Field(None, description="Escolha feita pelo jogador 2")
    error: Optional[str] = Field(None, description="Tipo do erro: TIMEOUT, EXECUTION_ERROR, SESSION_NOT_FOUND ou None")
    errorDetail: Optional[str] = Field(None, description="Mensagem detalhada do erro")

    @classmethod
    def create(cls, result: dict):
        return cls(
            player1Choice=result.get("player1Choice"),
            player2Choice=result.get("player2Choice"),
            error=result.get("error"),
            errorDetail=result.get("errorDetail"),
        )