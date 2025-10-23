from pydantic import BaseModel, Field
from typing import Literal

# DTO que vai ser recebido na requisição. O próprio BaseModel faz a validação e atribuição
class ValidateRequest(BaseModel):
    code: str = Field(..., description="Função enviada pelo aluno")
    assistantStyle: str = Field(..., description="estilo do agente")
    functionName: str = Field(..., description="qual função está sendo analisada")
    gameName: Literal["JOKENPO", "BITS"] # apenas os jogos suportados

class ValidateResponse(BaseModel):
    valid: bool # indica se a validação foi bem sucedida
    answer: str # Retorna a resposta
    thought: str # Retorna o pensamento

    # Método de classe para facilitar a criação da instância
    @classmethod
    def create(cls, valid: bool, answer: str, thought: str):
        return cls(valid=valid, answer=answer, thought=thought)