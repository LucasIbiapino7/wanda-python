from typing import Protocol, Dict, Any, Tuple
from .registry import REGISTRY, GameSpec
from .pipelines.jokenpo import JokenpoPipeline
from .pipelines.bits.pipeline import BitsPipeline
import logging

logger = logging.getLogger(__name__)

class GameFeedbackPipeline(Protocol):
    async def feedback(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> dict:
        """
        Retorna dict padronizado:
        {
          "valid": bool,
          "answer": str,
          "thought": str
        }
        """
    async def run(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        """
        Execução de testes do jogo (assinatura + testes).
        Retorna:
        {
          "valid": bool,
          "answer": str,
          "thought": str
        }
        """
    async def validate(self, code: str, assistant_style: str, function_name: str, openai_api_key: str) -> Dict[str, Any]:
        """
        Validação completa do jogo (assinatura + testes finais).
        Retorna:
        {
          "valid": bool,
          "answer": str,
          "thought": str
        }
        """

def resolve_pipeline(game_name: str, function_name: str) -> Tuple[GameSpec, GameFeedbackPipeline]:
    spec = REGISTRY.get(game_name)
    if not spec:
        logger.error('Jogo nao suportado. game=%s', game_name)
        raise ValueError(f"Jogo não suportado: {game_name}")

    if function_name not in spec.functions:
        logger.error('Funcao invalida para o jogo. game=%s function=%s', game_name, function_name)
        raise ValueError(f"Função '{function_name}' não é válida para {game_name}")

    # Fábricas para cada jogo
    return spec, spec.pipeline_class(spec)

    logger.error('Pipeline nao encontrado. game=%s', game_name)
    raise ValueError(f"Pipeline não encontrado para {game_name}")