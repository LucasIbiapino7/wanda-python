from pydantic import BaseModel, Field
from typing import List, Optional

class RoundRequestDTO(BaseModel):
    player1Function: str = Field(..., description="Função enviada pelo jogador 1")
    player1Parameters: List[Optional[str]] = Field(..., description="Parâmetros para a função do jogador 1")
    player2Function: str = Field(..., description="Função enviada pelo jogador 2")
    player2Parameters: List[Optional[str]] = Field(..., description="Parâmetros para a função do jogador 2")

class RoundResponseDTO(BaseModel):
    player1Choice: str = Field(..., description="Escolha feita pelo jogador 1")
    player2Choice: str = Field(..., description="Escolha feita pelo jogador 2")

    @classmethod
    def create(cls, player1_choice: str, player2_choice: str):
        return cls(player1Choice=player1_choice, player2Choice=player2_choice)