from typing import Any, List, Optional
from pydantic import BaseModel, Field

class RoundBitsRequestDTO(BaseModel):
    player1Function: str = Field(..., description="Função enviada pelo jogador 1")
    player1Parameters: List[Any] = Field(..., description="Parâmetros (BITS) do jogador 1")
    player2Function: str = Field(..., description="Função enviada pelo jogador 2")
    player2Parameters: List[Any] = Field(..., description="Parâmetros (BITS) do jogador 2")


