from pydantic import BaseModel, Field

# DTO que vai ser recebido na requisição. O próprio BaseModel faz a validação e atribuição
class ValidateRequest(BaseModel):
    code: str = Field(..., description="Função enviada pelo aluno")

class ValidateResponse(BaseModel):
    valid: bool # indica se a validação foi bem sucedida
    errors: list[str] # Retorna as informações do Erro. Caso o Valid seja True, a lista vai vazia

    # Método de classe para facilitar a criação da instância
    @classmethod
    def create(cls, valid: bool, errors: list[str]):
        return cls(valid=valid, errors=errors)